import { apiFetch } from '../../src/utils/apiFetch.js'

export function fetchProductList(params) {
  return apiFetch('/api/v1/product', { query: params })
}

export function createProduct(data) {
  return apiFetch('/api/v1/product', {
    method: 'POST',
    body: data
  })
}

export function updateProduct(id, data) {
  return apiFetch(`/api/v1/product/${id}`, {
    method: 'PUT',
    body: data
  })
}

export function deleteProduct(id) {
  return apiFetch(`/api/v1/product/${id}`, {
    method: 'DELETE'
  })
}
