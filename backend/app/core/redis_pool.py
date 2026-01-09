import time
import redis
import asyncio  # 必须导入 asyncio
import redis.asyncio as aioredis # 必须导入 aioredis
from redis.connection import ConnectionPool # 同步连接池
from app.boot import settings, logger  
from typing import Dict, Set, AsyncGenerator,Optional
from redis.asyncio import Redis

# 频道名称，如果需要在其他地方使用，可以放到配置中
subscribeChannel = "celery_task_updates"

class RedisPool:
    # 静态变量，用于存储同步Redis连接池
    _sync_pool_instance = None
    # 静态变量，用于存储异步Redis连接池
    _async_pool_instance = None
    # 异步初始化锁，延迟创建避免 gevent 冲突
    _async_init_lock = None 

    _pubsub_manager = None

    # 私有构造函数，防止外部直接实例化，因为我们使用类方法来管理单例连接池
    def __init__(self):
        # 这个构造函数通常不会被直接调用，除非通过 get_redis() 的内部逻辑
        pass 

    @classmethod
    def _initialize_sync_pool(cls):
        """内部方法：初始化同步Redis连接池（带异常处理和重试机制）"""
        if cls._sync_pool_instance is None:
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"正在初始化同步Redis连接池... (尝试 {attempt + 1}/{max_retries})")
                    logger.info(f"Redis配置: host={settings.redis.host}, port={settings.redis.port}")
                    
                    cls._sync_pool_instance = ConnectionPool(
                        host=settings.redis.host,
                        port=settings.redis.port,
                        password=settings.redis.password if settings.redis.password else None,
                        decode_responses=True,
                        db=0,
                        max_connections=100,
                        socket_connect_timeout=5,
                        socket_keepalive=True,
                        health_check_interval=30,
                        retry_on_timeout=True
                    )
                    
                    # 测试连接
                    test_client = redis.Redis(connection_pool=cls._sync_pool_instance)
                    test_client.ping()
                    logger.info("✓ 同步Redis连接池初始化成功并测试连接正常")
                    return
                    
                except Exception as e:
                    logger.error(f"Redis 连接池初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    cls._sync_pool_instance = None
                    
                    if attempt < max_retries - 1:
                        logger.info(f"将在 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.critical(f"Redis 连接池初始化失败，已达到最大重试次数！配置: host={settings.redis.host}, port={settings.redis.port}")
                        raise ConnectionError(f"无法连接到 Redis: host={settings.redis.host}, port={settings.redis.port}")

    @classmethod
    def get_redis(cls):
        """
        获取一个同步的 Redis 客户端实例。
        这个方法现在是同步的。
        """
        cls._initialize_sync_pool()  # 确保同步连接池已初始化
        
        if cls._sync_pool_instance is None:
            raise ConnectionError(
                f"Redis 连接池未初始化！无法获取 Redis 客户端。"
                f"配置: host={settings.redis.host}, port={settings.redis.port}"
            )
        
        return redis.Redis(connection_pool=cls._sync_pool_instance)

    @classmethod
    async def _initialize_async_pool_instance(cls):
        """
        内部方法：异步初始化异步Redis连接池。
        此方法必须在一个asyncio事件循环中被 await 调用。
        """
        # 延迟创建锁，避免 gevent 冲突
        if cls._async_init_lock is None:
            cls._async_init_lock = asyncio.Lock()
        
        async with cls._async_init_lock: # 使用异步锁确保只初始化一次
            if cls._async_pool_instance is None:
                cls._async_pool_instance = aioredis.ConnectionPool.from_url(
                    f"redis://:{settings.redis.password}@{settings.redis.host}:{settings.redis.port}/0",
                    max_connections=100,
                    decode_responses=True
                )
                logger.info("Asynchronous Redis pool initialized.")

    @classmethod
    async def get_async_redis(cls):
        """
        获取一个异步的 Redis 客户端实例。
        如果异步连接池尚未初始化，它将在此方法中被异步初始化。
        """
        if cls._async_pool_instance is None:
            await cls._initialize_async_pool_instance() # 异步初始化，这里必须 await
        return aioredis.Redis(connection_pool=cls._async_pool_instance)

    @classmethod
    def publish(cls, channel: str, message: str):
        """
        同步发布消息到 Redis 频道。
        这个方法是同步的。
        """
        r = cls.get_redis() # 获取同步 Redis 客户端
        result = r.publish(channel, message) # 直接调用同步 publish 方法
        logger.debug(f"Published message to channel {channel}, {result} subscribers")

    @classmethod
    async def async_publish(cls, channel: str, message: str):
        """
        异步发布消息到 Redis 频道。
        此方法必须在异步上下文 (即被 async def 函数调用并 await) 中使用。
        """
        try:
            r = await cls.get_async_redis() # 获取异步 Redis 客户端，这里必须 await
            logger.info(f"异步发布消息到频道 {channel}: {message}")
            await r.publish(channel, message) # 调用异步 publish 方法，这里必须 await
        except Exception as e:
            logger.error(f"异步发布消息到频道 {channel} 失败: {e}")
            raise # 重新抛出异常，以便Celery或上层捕获

    @classmethod
    async def async_listen(cls, channel: str):
        """
        异步监听 Redis 频道消息。
        此方法必须在异步上下文中被 await 调用。
        """
        r = None
        pubsub = None
        try:
            r = await cls.get_async_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe(channel)
            last_active = time.time()
            
            # 发送初始心跳
            yield {"event": "heartbeat", "data": "ping"}
            
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=1.0  # 1秒超时
                    )
                    
                    if message is not None:
                        last_active = time.time()
                        logger.info(f"从频道 {channel} 接收到消息: {message}")
                        yield message['data']
                    else:
                        # 每15秒发送一次心跳（避免代理超时）
                        if time.time() - last_active > 15:
                            last_active = time.time()
                            yield {"event": "heartbeat", "data": "ping"}
                            
                except asyncio.TimeoutError:
                    # 定期检查连接状态
                    if time.time() - last_active > 15:
                        last_active = time.time()
                        yield {"event": "heartbeat", "data": "ping"}
                    continue
                except asyncio.CancelledError:
                    logger.info(f"Redis listen cancelled for channel {channel}")
                    break
                except Exception as e:
                    logger.error(f"Redis listen error for channel {channel}: {e}")
                    # 在错误时等待一下再继续
                    await asyncio.sleep(1)
                    continue
                    
                await asyncio.sleep(0.1)  # 避免CPU空转
                
        except Exception as e:
            logger.error(f"Redis async_listen setup error: {e}")
        finally:
            # 清理资源
            if pubsub:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception as e:
                    logger.error(f"Error closing pubsub: {e}")

    @classmethod
    async def get_pubsub_manager(cls):
        """获取单例订阅管理器"""
        if cls._pubsub_manager is None:
            cls._pubsub_manager = RedisPubSubManager()
            await cls._pubsub_manager.initialize()
        return cls._pubsub_manager
    
    @classmethod
    async def async_listen_pubsub(cls, channel: str):
        """
        使用单例模式监听频道
        """
        manager = await cls.get_pubsub_manager()
        async for message in manager.listen(channel):
            yield message

    @classmethod
    async def close_pubsub_manager(cls):
        """关闭订阅管理器（用于应用退出时）"""
        if cls._pubsub_manager:
            await cls._pubsub_manager.stop()

class RedisPubSubManager:
    _instance = None
    _redis_client: Optional[Redis] = None
    _pubsub = None
    _channel_queues: Dict[str, Set[asyncio.Queue]] = {}
    _is_running = False
    _worker_task = None
    _reconnect_attempts = 0
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 3  # seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("创建新的RedisPubSubManager单例实例")
        return cls._instance

    async def initialize(self):
        """初始化Redis连接（带重试机制）"""
        if self._redis_client is None or not await self._check_connection():
            await self._reconnect()

    async def _check_connection(self) -> bool:
        """检查Redis连接是否有效"""
        try:
            if self._redis_client:
                await self._redis_client.ping()
                return True
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis连接检查失败")
        return False

    async def _reconnect(self):
        """重新连接Redis（带指数退避）"""
        while self._reconnect_attempts < self.MAX_RECONNECT_ATTEMPTS:
            try:
                # 清理旧连接
                if self._pubsub:
                    try:
                        await self._pubsub.close()
                    except Exception:
                        pass
                if self._redis_client:
                    try:
                        await self._redis_client.close()
                    except Exception:
                        pass

                # 创建新连接
                self._redis_client = aioredis.Redis(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    password=settings.redis.password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                self._pubsub = self._redis_client.pubsub()

                # 重新订阅所有频道
                if self._channel_queues:
                    channels = list(self._channel_queues.keys())
                    await self._pubsub.subscribe(*channels)
                    logger.info(f"成功重新订阅频道: {channels}")

                self._reconnect_attempts = 0
                return

            except Exception as e:
                self._reconnect_attempts += 1
                delay = min(self.RECONNECT_DELAY * (2 ** (self._reconnect_attempts - 1)), 30)
                logger.error(f"Redis连接失败(尝试 {self._reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS}): {e}, {delay}秒后重试...")
                await asyncio.sleep(delay)

        raise ConnectionError(f"无法连接到Redis，已达到最大重试次数 {self.MAX_RECONNECT_ATTEMPTS}")

    async def start(self):
        """启动消息分发工作器"""
        if not self._is_running:
            logger.info("启动Redis PubSub消息分发工作器...")
            await self.initialize()
            self._is_running = True
            self._worker_task = asyncio.create_task(self._message_distributor())
            logger.info("Redis PubSub消息分发工作器已启动")

    async def stop(self):
        """停止工作器并清理资源"""
        if self._is_running:
            logger.info("正在停止Redis PubSub消息分发工作器...")
            self._is_running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    logger.info("Redis PubSub消息分发工作器已取消")

            if self._pubsub:
                try:
                    logger.info("正在关闭PubSub连接...")
                    await self._pubsub.close()
                    logger.info("PubSub连接已关闭")
                except Exception as e:
                    logger.error(f"关闭pubsub错误: {e}")

            if self._redis_client:
                try:
                    logger.info("正在关闭Redis客户端连接...")
                    await self._redis_client.close()
                    logger.info("Redis客户端连接已关闭")
                except Exception as e:
                    logger.error(f"关闭Redis客户端错误: {e}")

    async def subscribe(self, *channels: str) -> Dict[str, asyncio.Queue]:
        """
        订阅一个或多个频道，返回每个频道的消息队列
        同一个频道的多个消费者共享同一个Redis订阅
        """
        await self.start()
        queues = {}

        for channel in channels:
            if channel not in self._channel_queues:
                logger.info(f"首次订阅频道[{channel}]，正在向Redis服务器发起订阅...")
                self._channel_queues[channel] = set()
                try:
                    await self._pubsub.subscribe(channel)
                    logger.info(f"频道[{channel}] Redis订阅成功")
                except Exception as e:
                    logger.error(f"订阅频道[{channel}]失败: {e}")
                    await self._reconnect()
                    await self._pubsub.subscribe(channel)

            # 为这个消费者创建消息队列
            queue = asyncio.Queue(maxsize=100)  # 限制队列大小防止内存溢出
            self._channel_queues[channel].add(queue)
            queues[channel] = queue
            logger.info(f"新增频道[{channel}]的消费者，当前消费者数量: {len(self._channel_queues[channel])}")

        return queues

    async def unsubscribe(self, channel: str, queue: asyncio.Queue):
        """取消订阅指定频道的指定队列"""
        if channel in self._channel_queues and queue in self._channel_queues[channel]:
            logger.debug(f"移除频道[{channel}]的一个消费者")
            self._channel_queues[channel].remove(queue)

            # 如果没有消费者了，取消Redis订阅
            if not self._channel_queues[channel]:
                logger.info(f"频道[{channel}]没有消费者了，正在取消Redis订阅...")
                try:
                    await self._pubsub.unsubscribe(channel)
                except Exception as e:
                    logger.error(f"取消订阅频道[{channel}]失败: {e}")
                del self._channel_queues[channel]
                logger.info(f"频道[{channel}] Redis订阅已取消")

    async def _message_distributor(self):
        """消息分发工作器（增强版）"""
        logger.info("Redis消息分发工作器开始运行")
        last_heartbeat = time.time()
        message_count = 0
        HEARTBEAT_INTERVAL = 15  # seconds

        while self._is_running:
            try:
                # 确保连接有效
                if not await self._check_connection():
                    logger.warning("Redis连接异常，尝试重新连接...")
                    await self._reconnect()
                    continue

                # 确保有活跃订阅
                if not self._channel_queues:
                    await asyncio.sleep(1)
                    continue

                # 获取消息（带超时）
                try:
                    message = await asyncio.wait_for(
                        self._pubsub.get_message(
                            ignore_subscribe_messages=True,
                            timeout=1.0
                        ),
                        timeout=2.0
                    )
                except (redis.ConnectionError, redis.TimeoutError) as e:
                    logger.error(f"获取消息时连接错误: {e}")
                    await self._reconnect()
                    continue
                except Exception as e:
                    logger.error(f"获取消息时未知错误: {e}")
                    await asyncio.sleep(1)
                    continue

                # 处理心跳
                current_time = time.time()
                if current_time - last_heartbeat > HEARTBEAT_INTERVAL:
                    last_heartbeat = current_time
                    for channel, queues in self._channel_queues.items():
                        for queue in list(queues):
                            try:
                                await queue.put({"event": "heartbeat", "data": "ping"})
                            except Exception as e:
                                logger.warning(f"发送心跳到频道[{channel}]失败: {e}")

                # 处理有效消息
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    message_count += 1

                    logger.debug(f"Received message #{message_count} on channel [{channel}]")

                    if channel in self._channel_queues:
                        for queue in list(self._channel_queues[channel]):
                            try:
                                queue.put_nowait(data)
                            except asyncio.QueueFull:
                                logger.warning(f"频道[{channel}]的消费者队列已满，丢弃消息")
                    else:
                        logger.warning(f"频道[{channel}]没有订阅者")

                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                logger.info("Redis消息分发工作器收到取消信号")
                break
            except Exception as e:
                logger.error(f"消息分发器错误: {e}")
                await asyncio.sleep(1)

        logger.info(f"Redis消息分发工作器停止运行，共处理了{message_count}条消息")

    async def listen(self, *channels: str) -> AsyncGenerator:
        """
        监听一个或多个频道的消息
        返回格式: {"channel": 频道名, "data": 消息内容}
        """
        logger.info(f"开始监听频道: {channels}")
        queues = await self.subscribe(*channels)
        
        try:
            # 发送初始心跳
            initial_heartbeat = {"event": "heartbeat", "data": "ping"}
            for channel in channels:
                if channel in queues:
                    try:
                        await queues[channel].put(initial_heartbeat)
                    except Exception as e:
                        logger.warning(f"发送初始心跳到频道[{channel}]失败: {e}")
            yield {"event": "init", "data": {"channels": list(channels)}}

            while True:
                for channel, queue in queues.items():
                    try:
                        # 使用较短的超时时间轮询多个队列
                        message = await asyncio.wait_for(queue.get(), timeout=0.1)
                        # yield {"channel": channel, "data": message}
                        if len(channels) == 1:
                            yield message
                        else:
                            yield {"channel": channel, "data": message}
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"处理频道[{channel}]消息时出错: {e}")
                        await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("监听被取消")
        finally:
            logger.info("正在取消监听...")
            for channel, queue in queues.items():
                try:
                    await self.unsubscribe(channel, queue)
                except Exception as e:
                    logger.error(f"取消订阅频道[{channel}]时出错: {e}")
            logger.info("所有频道监听已取消")