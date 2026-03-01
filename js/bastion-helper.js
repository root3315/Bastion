/**
 * Bastion JavaScript Helper Module
 * 
 * Provides utility functions for JSON manipulation, file operations,
 * and network helpers to complement the Python core.
 * 
 * @module bastion-helper
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');
const http = require('http');

/**
 * Bastion Helper Class
 */
class BastionHelper {
  /**
   * Create a BastionHelper instance
   * @param {Object} options - Configuration options
   * @param {string} options.logLevel - Logging level (debug, info, warn, error)
   * @param {string} options.outputDir - Output directory for files
   */
  constructor(options = {}) {
    this.logLevel = options.logLevel || 'info';
    this.outputDir = options.outputDir || './reports';
    this.version = '1.0.0';
  }

  /**
   * Log a message with level
   * @param {string} level - Log level
   * @param {string} message - Message to log
   * @param {Object} data - Additional data
   */
  log(level, message, data = null) {
    const levels = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.logLevel);
    const messageLevelIndex = levels.indexOf(level);

    if (messageLevelIndex >= currentLevelIndex) {
      const timestamp = new Date().toISOString();
      const logEntry = {
        timestamp,
        level: level.toUpperCase(),
        message,
        ...(data && { data })
      };
      console.log(JSON.stringify(logEntry));
    }
  }

  /**
   * Validate and sanitize JSON input
   * @param {any} data - Data to validate
   * @param {Object} schema - Validation schema
   * @returns {Object} Validation result
   */
  validateJson(data, schema = null) {
    const result = {
      valid: true,
      errors: [],
      sanitized: null
    };

    try {
      // Parse if string
      let parsed = typeof data === 'string' ? JSON.parse(data) : data;
      
      // Basic type check
      if (typeof parsed !== 'object' || parsed === null) {
        result.valid = false;
        result.errors.push('Data must be an object');
        return result;
      }

      // Schema validation
      if (schema) {
        for (const [field, rules] of Object.entries(schema)) {
          if (rules.required && !(field in parsed)) {
            result.valid = false;
            result.errors.push(`Missing required field: ${field}`);
          }
          
          if (field in parsed && rules.type) {
            const actualType = typeof parsed[field];
            if (rules.type === 'array' && !Array.isArray(parsed[field])) {
              result.valid = false;
              result.errors.push(`Field ${field} must be an array`);
            } else if (rules.type !== 'array' && actualType !== rules.type) {
              result.valid = false;
              result.errors.push(`Field ${field} must be ${rules.type}`);
            }
          }
          
          if (field in parsed && rules.maxLength && typeof parsed[field] === 'string') {
            if (parsed[field].length > rules.maxLength) {
              result.valid = false;
              result.errors.push(`Field ${field} exceeds maximum length`);
            }
          }
        }
      }

      // Sanitize - remove potentially dangerous keys
      const dangerousKeys = ['__proto__', 'constructor', 'prototype'];
      result.sanitized = this._removeKeys(parsed, dangerousKeys);

    } catch (error) {
      result.valid = false;
      result.errors.push(`Parse error: ${error.message}`);
    }

    return result;
  }

  /**
   * Remove specified keys from an object recursively
   * @param {Object} obj - Object to process
   * @param {string[]} keys - Keys to remove
   * @returns {Object} Cleaned object
   * @private
   */
  _removeKeys(obj, keys) {
    if (!obj || typeof obj !== 'object') return obj;
    
    if (Array.isArray(obj)) {
      return obj.map(item => this._removeKeys(item, keys));
    }

    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      if (!keys.includes(key)) {
        result[key] = this._removeKeys(value, keys);
      }
    }
    return result;
  }

  /**
   * Generate a secure random token
   * @param {number} length - Token length
   * @returns {string} Random token
   */
  generateToken(length = 32) {
    return crypto.randomBytes(length).toString('hex');
  }

  /**
   * Generate a hash of data
   * @param {string} data - Data to hash
   * @param {string} algorithm - Hash algorithm
   * @returns {string} Hash string
   */
  hash(data, algorithm = 'sha256') {
    return crypto.createHash(algorithm).update(data).digest('hex');
  }

  /**
   * Read a file safely
   * @param {string} filePath - Path to file
   * @param {Object} options - Read options
   * @returns {Object} Read result
   */
  readFile(filePath, options = {}) {
    const result = {
      success: false,
      content: null,
      error: null
    };

    try {
      // Path traversal check
      const resolvedPath = path.resolve(filePath);
      const baseDir = path.resolve(options.baseDir || process.cwd());
      
      if (!resolvedPath.startsWith(baseDir)) {
        result.error = 'Path traversal not allowed';
        return result;
      }

      const encoding = options.encoding || 'utf8';
      result.content = fs.readFileSync(resolvedPath, encoding);
      result.success = true;

      this.log('debug', 'File read successfully', { path: resolvedPath });

    } catch (error) {
      result.error = error.message;
      this.log('error', 'File read failed', { path: filePath, error: error.message });
    }

    return result;
  }

  /**
   * Write a file safely
   * @param {string} filePath - Path to file
   * @param {string} content - Content to write
   * @param {Object} options - Write options
   * @returns {Object} Write result
   */
  writeFile(filePath, content, options = {}) {
    const result = {
      success: false,
      error: null
    };

    try {
      // Path traversal check
      const resolvedPath = path.resolve(filePath);
      const baseDir = path.resolve(options.baseDir || this.outputDir);
      
      if (!resolvedPath.startsWith(baseDir)) {
        result.error = 'Path traversal not allowed';
        return result;
      }

      // Create directory if needed
      const dir = path.dirname(resolvedPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      const encoding = options.encoding || 'utf8';
      fs.writeFileSync(resolvedPath, content, encoding);
      result.success = true;

      this.log('info', 'File written successfully', { path: resolvedPath });

    } catch (error) {
      result.error = error.message;
      this.log('error', 'File write failed', { path: filePath, error: error.message });
    }

    return result;
  }

  /**
   * Read and parse a JSON file
   * @param {string} filePath - Path to JSON file
   * @returns {Object} Parse result
   */
  readJsonFile(filePath) {
    const fileResult = this.readFile(filePath);
    
    if (!fileResult.success) {
      return {
        success: false,
        data: null,
        error: fileResult.error
      };
    }

    try {
      const data = JSON.parse(fileResult.content);
      return {
        success: true,
        data,
        error: null
      };
    } catch (error) {
      return {
        success: false,
        data: null,
        error: `JSON parse error: ${error.message}`
      };
    }
  }

  /**
   * Write data as JSON file
   * @param {string} filePath - Path to file
   * @param {Object} data - Data to write
   * @param {Object} options - Write options
   * @returns {Object} Write result
   */
  writeJsonFile(filePath, data, options = {}) {
    const content = JSON.stringify(data, null, options.pretty ? 2 : 0);
    return this.writeFile(filePath, content, options);
  }

  /**
   * Make an HTTP request
   * @param {string} url - URL to fetch
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Request result
   */
  async fetch(url, options = {}) {
    return new Promise((resolve) => {
      const result = {
        success: false,
        statusCode: null,
        data: null,
        error: null
      };

      try {
        const parsedUrl = new URL(url);
        
        // Validate URL
        if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
          result.error = 'Only HTTP and HTTPS protocols allowed';
          resolve(result);
          return;
        }

        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const reqOptions = {
          method: options.method || 'GET',
          headers: options.headers || {},
          timeout: options.timeout || 10000
        };

        const req = client.request(url, reqOptions, (res) => {
          result.statusCode = res.statusCode;
          
          let chunks = [];
          res.on('data', chunk => chunks.push(chunk));
          res.on('end', () => {
            const body = Buffer.concat(chunks).toString();
            
            try {
              result.data = JSON.parse(body);
            } catch {
              result.data = body;
            }
            
            result.success = res.statusCode >= 200 && res.statusCode < 300;
            resolve(result);
          });
        });

        req.on('error', error => {
          result.error = error.message;
          resolve(result);
        });

        req.on('timeout', () => {
          req.destroy();
          result.error = 'Request timeout';
          resolve(result);
        });

        if (options.body) {
          req.write(typeof options.body === 'string' ? options.body : JSON.stringify(options.body));
        }

        req.end();

      } catch (error) {
        result.error = error.message;
        resolve(result);
      }
    });
  }

  /**
   * Validate an email address
   * @param {string} email - Email to validate
   * @returns {boolean} Is valid
   */
  validateEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
  }

  /**
   * Validate an IP address
   * @param {string} ip - IP to validate
   * @param {number} version - IP version (4 or 6)
   * @returns {boolean} Is valid
   */
  validateIp(ip, version = null) {
    if (version === 4 || version === null) {
      const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (ipv4Pattern.test(ip)) {
        const octets = ip.split('.');
        return octets.every(octet => {
          const num = parseInt(octet, 10);
          return num >= 0 && num <= 255;
        });
      }
    }

    if (version === 6 || version === null) {
      const ipv6Pattern = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
      if (ipv6Pattern.test(ip)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Sleep for a specified duration
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise<void>}
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Retry a function with exponential backoff
   * @param {Function} fn - Function to retry
   * @param {Object} options - Retry options
   * @returns {Promise<any>} Function result
   */
  async retry(fn, options = {}) {
    const maxRetries = options.maxRetries || 3;
    const baseDelay = options.baseDelay || 1000;
    const factor = options.factor || 2;

    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        
        if (attempt < maxRetries) {
          const delay = baseDelay * Math.pow(factor, attempt);
          this.log('warn', 'Retry attempt', { attempt: attempt + 1, delay });
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Format bytes to human-readable string
   * @param {number} bytes - Bytes to format
   * @param {number} decimals - Decimal places
   * @returns {string} Formatted string
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * Get current timestamp in ISO format
   * @returns {string} ISO timestamp
   */
  timestamp() {
    return new Date().toISOString();
  }
}

/**
 * Create a BastionHelper instance with default options
 * @param {Object} options - Configuration options
 * @returns {BastionHelper} Helper instance
 */
function createHelper(options = {}) {
  return new BastionHelper(options);
}

// Export for Node.js
module.exports = {
  BastionHelper,
  createHelper
};

// Export for ES modules (if used with transpiler)
if (typeof module !== 'undefined' && module.exports) {
  module.exports.default = createHelper;
}
