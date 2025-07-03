import wsManagerInstance from '@/api/chat.js';

export class FileTransferAPI {
  static async sendFile(file, recipientUsername) {
    try {
      const fileData = await this.fileToBase64(file);
      
      // 改进：使用特殊的消息格式标识
      const fileMessage = `[FILE]${JSON.stringify({
        type: 'file',
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        fileData: fileData
      })}`;

      const success = wsManagerInstance.sendMessage(recipientUsername, fileMessage);
      return { success, fileName: file.name };
    } catch (error) {
      console.error('文件发送失败:', error);
      return { success: false, error: error.message };
    }
  }

  static async fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  static downloadFile(fileData, fileName) {
    const link = document.createElement('a');
    link.href = fileData;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // 检查是否是文件消息
  static isFileMessage(content) {
    return typeof content === 'string' && content.startsWith('[FILE]');
  }

  // 解析文件消息
  static parseFileMessage(content) {
    if (!this.isFileMessage(content)) return null;
    try {
      return JSON.parse(content.substring(6)); // 去掉 '[FILE]' 前缀
    } catch (error) {
      console.error('解析文件消息失败:', error);
      return null;
    }
  }
}