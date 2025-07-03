/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 0);
/******/ })
/************************************************************************/
/******/ ({

/***/ "./electron/main.js":
/*!**************************!*\
  !*** ./electron/main.js ***!
  \**************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

eval("const { app, BrowserWindow, ipcMain } = __webpack_require__(/*! electron */ \"electron\")\r\nconst path = __webpack_require__(/*! path */ \"path\")\r\n\r\nlet mainWindow\r\n\r\nfunction createWindow() {\r\n  mainWindow = new BrowserWindow({\r\n    width: 400,\r\n    height: 350,\r\n    resizable: false,\r\n    frame: false,\r\n    center: true,\r\n    show: false,\r\n    webPreferences: {\r\n      nodeIntegration: true,\r\n      contextIsolation: false,\r\n      webSecurity: false,\r\n      preload: path.join(__dirname, 'preload.js')\r\n    }\r\n  })\r\n\r\n  // 开发环境加载本地服务器，生产环境加载打包后的文件\r\n  const isDev = \"development\" === 'development'\r\n  if (isDev) {\r\n    mainWindow.loadURL('http://localhost:8080')\r\n    // 开发环境下打开开发者工具\r\n    // mainWindow.webContents.openDevTools()\r\n  } else {\r\n    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))\r\n  }\r\n\r\n  // 窗口加载完成后显示\r\n  mainWindow.once('ready-to-show', () => {\r\n    mainWindow.show()\r\n  })\r\n\r\n  // 窗口关闭时清理\r\n  mainWindow.on('closed', () => {\r\n    mainWindow = null\r\n  })\r\n}\r\n\r\n// 应用准备就绪时创建窗口\r\napp.whenReady().then(createWindow)\r\n\r\n// 所有窗口关闭时退出应用（macOS除外）\r\napp.on('window-all-closed', () => {\r\n  if (process.platform !== 'darwin') {\r\n    app.quit()\r\n  }\r\n})\r\n\r\n// macOS激活时重新创建窗口\r\napp.on('activate', () => {\r\n  if (BrowserWindow.getAllWindows().length === 0) {\r\n    createWindow()\r\n  }\r\n})\r\n\r\n// 处理渲染进程发送的窗口控制消息\r\nipcMain.handle('window-close', () => {\r\n  if (mainWindow) {\r\n    mainWindow.close()\r\n  }\r\n})\r\n\r\nipcMain.handle('window-minimize', () => {\r\n  if (mainWindow) {\r\n    mainWindow.minimize()\r\n  }\r\n})\n\n//# sourceURL=webpack:///./electron/main.js?");

/***/ }),

/***/ 0:
/*!********************************!*\
  !*** multi ./electron/main.js ***!
  \********************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

eval("module.exports = __webpack_require__(/*! D:\\.AAAAAlearning\\college lecture\\CodeDesignLecture\\SecurityChat\\frontend\\electron\\main.js */\"./electron/main.js\");\n\n\n//# sourceURL=webpack:///multi_./electron/main.js?");

/***/ }),

/***/ "electron":
/*!***************************!*\
  !*** external "electron" ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports) {

eval("module.exports = require(\"electron\");\n\n//# sourceURL=webpack:///external_%22electron%22?");

/***/ }),

/***/ "path":
/*!***********************!*\
  !*** external "path" ***!
  \***********************/
/*! no static exports found */
/***/ (function(module, exports) {

eval("module.exports = require(\"path\");\n\n//# sourceURL=webpack:///external_%22path%22?");

/***/ })

/******/ });