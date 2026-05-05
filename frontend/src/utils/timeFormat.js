/**
 * 时间格式化工具函数
 * 将后端返回的时间字符串转换为本地时区并格式化显示
 */

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm:ss
 * @param {string} dateStr - 后端返回的时间字符串
 * @returns {string} 格式化后的时间字符串，精确到秒
 */
export const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  
  try {
    const date = new Date(dateStr);
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return dateStr; // 如果无法解析，返回原始字符串
    }
    
    // 格式化为本地时间 YYYY-MM-DD HH:mm:ss
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    console.error('时间格式化错误:', error);
    return dateStr;
  }
};

/**
 * 格式化日期为 YYYY-MM-DD（仅日期）
 * @param {string} dateStr - 后端返回的时间字符串
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  
  try {
    const date = new Date(dateStr);
    
    if (isNaN(date.getTime())) {
      return dateStr;
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  } catch (error) {
    console.error('日期格式化错误:', error);
    return dateStr;
  }
};
