"use strict";
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("widgets", {
  invoke: (action, payload = {}) =>
    ipcRenderer.invoke("widgets", action, payload),
  subscribe: (callback) => {
    const listener = (_e, data) => callback(data);
    ipcRenderer.on("snapshot", listener);
    return () => ipcRenderer.removeListener("snapshot", listener);
  },
});
