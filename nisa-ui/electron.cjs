const { app, BrowserWindow, shell, Menu } = require('electron')
const path = require('path')
const { exec } = require('child_process')

const isDev = process.env.NODE_ENV === 'development'

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#080c18',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
    icon: path.join(__dirname, 'public', 'nisa-icon.png'),
    title: 'NISA — Network Intelligence Security Assistant',
  })

  if (isDev) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(path.join(__dirname, 'dist', 'index.html'))
    win.webContents.on('did-finish-load', () => {
      win.webContents.executeJavaScript('window.location.hash = "/"')
    })
  }

  // Open external links in browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // Custom menu
  const menu = Menu.buildFromTemplate([
    {
      label: 'NISA',
      submenu: [
        { label: 'About NISA v0.3.0', enabled: false },
        { type: 'separator' },
        { label: 'Quit', accelerator: 'Cmd+Q', click: () => app.quit() }
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', accelerator: 'Cmd+R', click: () => win.reload() },
        { label: 'Toggle DevTools', accelerator: 'Cmd+Option+I',
          click: () => win.webContents.toggleDevTools() },
        { type: 'separator' },
        { label: 'Actual Size', accelerator: 'Cmd+0',
          click: () => win.webContents.setZoomLevel(0) },
        { label: 'Zoom In', accelerator: 'Cmd+Plus',
          click: () => win.webContents.setZoomLevel(
            win.webContents.getZoomLevel() + 0.5) },
        { label: 'Zoom Out', accelerator: 'Cmd+-',
          click: () => win.webContents.setZoomLevel(
            win.webContents.getZoomLevel() - 0.5) },
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { label: 'Cut', accelerator: 'Cmd+X', role: 'cut' },
        { label: 'Copy', accelerator: 'Cmd+C', role: 'copy' },
        { label: 'Paste', accelerator: 'Cmd+V', role: 'paste' },
        { label: 'Select All', accelerator: 'Cmd+A', role: 'selectAll' },
      ]
    }
  ])
  Menu.setApplicationMenu(menu)
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
