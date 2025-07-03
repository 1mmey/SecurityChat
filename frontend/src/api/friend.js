import { 
  getAuthHeadersForExport, 
  getFullApiUrl, 
  getUserInfo,
  isAuthenticated 
} from './auth.js'

const friendApiRequest = async (url, options = {}) => {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeadersForExport(),
      ...options.headers
    },
    ...options
  }
  
  try {
    const response = await fetch(getFullApiUrl(url), config)
    
    if (response.status === 401) {
      throw new Error('认证失败，请重新登录')
    }
    
    return response
  } catch (error) {
    console.error('好友API请求错误:', error)
    if (error.message.includes('认证失败')) {
      throw error
    }
    throw new Error('网络错误，请检查网络连接')
  }
}

export const getContacts = async (options = {}) => {
  try {
    const { skip = 0, limit = 100 } = options
    const url = `/me/contacts?skip=${skip}&limit=${limit}`
    const response = await friendApiRequest(url)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取好友列表失败: ${errorText}`)
    }
    
    const data = await response.json()
    
    return {
      success: true,
      data: data.map(contact => ({
        id: contact.id,
        user_id: contact.user_id,
        friend_id: contact.friend_id,
        status: contact.status,
        created_at: contact.created_at,
        friend: contact.friend ? {
          id: contact.friend.id,
          username: contact.friend.username,
          email: contact.friend.email,
          is_online: contact.friend.is_online || false,
          last_seen: contact.friend.last_seen,
          avatar: contact.friend.avatar || '',
          public_key: contact.friend.public_key || '',
          ip_address: contact.friend.ip_address || '',
          port: contact.friend.port || 0
        } : null
      }))
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取好友列表失败'
    }
  }
}

export const getPendingRequests = async (options = {}) => {
  try {
    const { skip = 0, limit = 100 } = options
    const url = `/me/contacts/pending?skip=${skip}&limit=${limit}`
    const response = await friendApiRequest(url)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取好友请求失败: ${errorText}`)
    }
    
    const data = await response.json()
    
    return {
      success: true,
      data: data.map(request => ({
        id: request.id,
        user_id: request.user_id,
        friend_id: request.friend_id,
        status: request.status,
        created_at: request.created_at,
        user: request.user ? {
          id: request.user.id,
          username: request.user.username,
          email: request.user.email,
          is_online: request.user.is_online || false,
          avatar: request.user.avatar || ''
        } : null
      }))
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取好友请求失败'
    }
  }
}

export const addContact = async (contactData) => {
  try {
    const response = await friendApiRequest('/me/contacts/', {
      method: 'POST',
      body: JSON.stringify(contactData)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      let errorMessage = '添加好友失败'
      
      try {
        const errorData = JSON.parse(errorText)
        errorMessage = errorData.detail || errorMessage
      } catch {
        errorMessage = errorText || errorMessage
      }
      
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data,
      message: '好友请求已发送'
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '添加好友失败'
    }
  }
}

export const acceptFriendRequest = async (contactId) => {
  try {
    console.log('接受好友请求，联系人ID:', contactId)
    
    const response = await friendApiRequest(`/me/contacts/${contactId}`, {
      method: 'PUT'
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      let errorMessage = '接受好友请求失败'
      
      try {
        const errorData = JSON.parse(errorText)
        errorMessage = errorData.detail || errorMessage
      } catch {
        errorMessage = errorText || errorMessage
      }
      
      throw new Error(errorMessage)
    }
    
    const data = await response.json()
    console.log('接受好友请求成功，返回数据:', data)
    
    return {
      success: true,
      data: data,
      message: '已接受好友请求'
    }
  } catch (error) {
    console.error('接受好友请求API错误:', error)
    return {
      success: false,
      message: error.message || '接受好友请求失败'
    }
  }
}

export const deleteFriendOrRequest = async (contactId) => {
  try {
    console.log('删除好友或请求，联系人ID:', contactId)
    
    const response = await friendApiRequest(`/me/contacts/${contactId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      let errorMessage = '操作失败'
      
      try {
        const errorData = JSON.parse(errorText)
        errorMessage = errorData.detail || errorMessage
      } catch {
        errorMessage = errorText || errorMessage
      }
      
      throw new Error(errorMessage)
    }
    
    console.log('删除操作成功')
    
    return {
      success: true,
      message: '操作成功'
    }
  } catch (error) {
    console.error('删除操作API错误:', error)
    return {
      success: false,
      message: error.message || '操作失败'
    }
  }
}

export const deleteContact = async (friendId) => {
  return await deleteFriendOrRequest(friendId)
}

export const getOnlineFriendsInfo = async () => {
  try {
    const response = await friendApiRequest('/me/contacts/online')
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取在线好友失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data.map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        is_online: user.is_online,
        ip_address: user.ip_address,
        port: user.port,
        public_key: user.public_key
      }))
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取在线好友失败'
    }
  }
}

export const getOnlineFriends = async () => {
  return await getOnlineFriendsInfo()
}

export const getFriendsOnlineStatus = async () => {
  return await getOnlineFriendsInfo()
}

export const searchUsers = async (query) => {
  try {
    const response = await friendApiRequest(`/users/search/${encodeURIComponent(query)}`)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`搜索用户失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data.map(user => ({
        id: user.id,
        username: user.username,
        is_online: user.is_online || false,
        avatar: user.avatar || ''
      }))
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '搜索用户失败'
    }
  }
}

export const searchUserByUsername = async (username) => {
  try {
    const result = await searchUsers(username)
    
    if (result.success) {
      const exactMatch = result.data.find(user => 
        user.username.toLowerCase() === username.toLowerCase()
      )
      
      if (exactMatch) {
        return {
          success: true,
          data: exactMatch
        }
      } else {
        return {
          success: false,
          message: '用户不存在'
        }
      }
    } else {
      return result
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '搜索用户失败'
    }
  }
}

export const updateConnectionInfo = async (port) => {
  try {
    const response = await friendApiRequest('/me/connection-info', {
      method: 'PUT',
      body: JSON.stringify({ port: port || 0 })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`更新连接信息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '更新连接信息失败'
    }
  }
}

export const getCurrentUserId = () => {
  const userInfo = getUserInfo()
  return userInfo ? userInfo.id : null
}

export const getCurrentUsername = () => {
  const userInfo = getUserInfo()
  return userInfo ? userInfo.username : null
}

export const getUserConnectionInfo = async (username) => {
  try {
    const response = await friendApiRequest(`/users/${username}/connection-info`)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取用户连接信息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: {
        username: username,
        public_key: data.public_key,
        ip_address: data.ip_address,
        port: data.port
      }
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取用户连接信息失败'
    }
  }
}

class FriendManager {
  constructor() {
    this.friends = new Map()
    this.onlineFriends = new Map()
    this.pendingRequests = new Map()
    this.contactIdToFriendId = new Map()
    this.friendIdToContactId = new Map()
  }

  updateFriend(friendData) {
    const friendId = friendData.friend_id || friendData.id
    const contactId = friendData.id
    
    const friend = {
      id: friendId,
      contactId: contactId,
      username: friendData.friend?.username || friendData.username,
      email: friendData.friend?.email || friendData.email,
      is_online: friendData.friend?.is_online || friendData.is_online || false,
      avatar: friendData.friend?.avatar || friendData.avatar || '',
      public_key: friendData.friend?.public_key || friendData.public_key || '',
      ip_address: friendData.friend?.ip_address || friendData.ip_address || '',
      port: friendData.friend?.port || friendData.port || 0,
      last_seen: friendData.friend?.last_seen || friendData.last_seen,
      status: friendData.status || 'accepted'
    }
    
    this.friends.set(friendId, friend)
    this.contactIdToFriendId.set(contactId, friendId)
    this.friendIdToContactId.set(friendId, contactId)
    
    if (friend.is_online) {
      this.onlineFriends.set(friendId, friend)
    } else {
      this.onlineFriends.delete(friendId)
    }
    
    console.log(`好友信息更新: ${friend.username} (ID: ${friendId}, 联系人ID: ${contactId})`)
  }

  removeFriend(identifier) {
    let friendId, contactId
    
    if (this.friends.has(identifier)) {
      friendId = identifier
      contactId = this.friendIdToContactId.get(friendId)
    } else if (this.contactIdToFriendId.has(identifier)) {
      contactId = identifier
      friendId = this.contactIdToFriendId.get(contactId)
    }
    
    if (friendId && contactId) {
      const friend = this.friends.get(friendId)
      this.friends.delete(friendId)
      this.onlineFriends.delete(friendId)
      this.contactIdToFriendId.delete(contactId)
      this.friendIdToContactId.delete(friendId)
      
      console.log(`好友已移除: ${friend?.username} (ID: ${friendId}, 联系人ID: ${contactId})`)
    }
  }

  updatePendingRequest(requestData) {
    const request = {
      id: requestData.id,
      user_id: requestData.user_id,
      friend_id: requestData.friend_id,
      status: requestData.status,
      created_at: requestData.created_at,
      user: requestData.user ? {
        id: requestData.user.id,
        username: requestData.user.username,
        email: requestData.user.email,
        is_online: requestData.user.is_online || false,
        avatar: requestData.user.avatar || ''
      } : null
    }
    
    this.pendingRequests.set(requestData.id, request)
    console.log(`待处理请求更新: ${request.user?.username} (请求ID: ${requestData.id})`)
  }

  removePendingRequest(requestId) {
    const request = this.pendingRequests.get(requestId)
    if (request) {
      this.pendingRequests.delete(requestId)
      console.log(`待处理请求已移除: ${request.user?.username} (请求ID: ${requestId})`)
    }
  }

  getFriend(friendId) {
    return this.friends.get(friendId)
  }

  getFriendByContactId(contactId) {
    const friendId = this.contactIdToFriendId.get(contactId)
    return friendId ? this.friends.get(friendId) : null
  }

  getContactIdByFriendId(friendId) {
    return this.friendIdToContactId.get(friendId)
  }

  getFriendByUsername(username) {
    for (const friend of this.friends.values()) {
      if (friend.username === username) {
        return friend
      }
    }
    return null
  }

  getAllFriends() {
    return Array.from(this.friends.values())
  }

  getOnlineFriends() {
    return Array.from(this.onlineFriends.values())
  }

  getPendingRequests() {
    return Array.from(this.pendingRequests.values())
  }

  updateFriendsStatus(friendsList) {
    friendsList.forEach(friend => {
      if (friend.status === 'accepted') {
        this.updateFriend(friend)
      }
    })
  }

  updatePendingRequestsStatus(requestsList) {
    requestsList.forEach(request => {
      this.updatePendingRequest(request)
    })
  }

  getFriendsStats() {
    return {
      totalFriends: this.friends.size,
      onlineFriends: this.onlineFriends.size,
      pendingRequests: this.pendingRequests.size
    }
  }

  clear() {
    this.friends.clear()
    this.onlineFriends.clear()
    this.pendingRequests.clear()
    this.contactIdToFriendId.clear()
    this.friendIdToContactId.clear()
    console.log('好友管理器已清空')
  }
}

export const friendManager = new FriendManager()

export default {
  getContacts,
  getPendingRequests,
  addContact,
  acceptFriendRequest,
  deleteFriendOrRequest,
  deleteContact,
  getOnlineFriendsInfo,
  getOnlineFriends,
  getFriendsOnlineStatus,
  searchUsers,
  searchUserByUsername,
  updateConnectionInfo,
  getCurrentUserId,
  getCurrentUsername,
  getUserConnectionInfo,
  friendManager
}