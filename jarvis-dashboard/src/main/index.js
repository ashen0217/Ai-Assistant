import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join, resolve } from 'path'
import { spawn } from 'child_process'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// ─────────────────────────────────────────────────────────────────────────────
//  Ghost Backend — Python Process Management
//  Spawns the FastAPI server as a child process and cleans it up on exit.
// ─────────────────────────────────────────────────────────────────────────────

let pythonProcess = null
let killTimer = null

/**
 * Spawns the Python/FastAPI backend.
 *
 * Dev mode  → runs `python server.py` from the repo root (2 levels up from
 *              jarvis-dashboard/src/main/index.js, i.e. d:/…/Ai-Assistant/)
 * Packaged  → runs core_engine.exe from the extraResources directory that
 *              electron-builder copies into the installed app bundle.
 */
function spawnPythonBackend() {
  let command, args, cwd

  if (!app.isPackaged) {
    // ── Development mode ──────────────────────────────────────────────────
    // __dirname = jarvis-dashboard/out/main/ (after electron-vite build)
    // Go up 3 levels to reach the repo root where server.py lives.
    const repoRoot = resolve(__dirname, '..', '..', '..', '..')
    command = 'python'
    args    = ['server.py']
    cwd     = repoRoot
    console.log(`[Backend] DEV — spawning: python server.py in ${cwd}`)
  } else {
    // ── Packaged mode ─────────────────────────────────────────────────────
    // process.resourcesPath points to the Resources/ folder inside the
    // installed app. electron-builder copies backend-dist/ there.
    const exePath = join(process.resourcesPath, 'backend-dist', 'core_engine.exe')
    command = exePath
    args    = []
    cwd     = join(process.resourcesPath, 'backend-dist')
    console.log(`[Backend] PACKAGED — spawning: ${exePath}`)
  }

  pythonProcess = spawn(command, args, {
    cwd,
    // Inherit environment so .env vars, OLLAMA_BASE_URL, etc. pass through.
    // In packaged mode the .env is placed alongside the exe by electron-builder.
    env: process.env,
    // detached: false keeps the child tied to the parent process group
    detached: false,
    // stdio pipes so we can log Python output to the Electron console
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  pythonProcess.stdout.on('data', (data) => {
    process.stdout.write(`[Python] ${data}`)
  })
  pythonProcess.stderr.on('data', (data) => {
    process.stderr.write(`[Python:ERR] ${data}`)
  })
  pythonProcess.on('close', (code) => {
    console.log(`[Backend] Python process exited with code ${code}`)
    pythonProcess = null
  })
  pythonProcess.on('error', (err) => {
    console.error(`[Backend] Failed to start Python process: ${err.message}`)
    if (!app.isPackaged) {
      console.error('[Backend] Make sure Python is in your PATH and venv is activated.')
    } else {
      console.error('[Backend] Make sure core_engine.exe exists in backend-dist/.')
    }
    pythonProcess = null
  })
}

/**
 * Gracefully shuts down the Python backend:
 *  1. Sends SIGTERM (allows FastAPI to flush and close mic stream)
 *  2. After 3 seconds, force-kills with SIGKILL if it didn't exit cleanly
 * This prevents orphaned processes that would hold the microphone.
 */
function killBackend() {
  if (!pythonProcess) return

  console.log('[Backend] Sending SIGTERM to Python process...')
  try {
    // On Windows, SIGTERM is translated to a kill by Node — this is fine.
    pythonProcess.kill('SIGTERM')
  } catch (_) {
    // Already dead — nothing to do
  }

  // Safety net: force-kill after 3s if process didn't respond to SIGTERM
  killTimer = setTimeout(() => {
    if (pythonProcess) {
      console.warn('[Backend] SIGTERM timeout — forcing SIGKILL...')
      try { pythonProcess.kill('SIGKILL') } catch (_) { /* already gone */ }
      pythonProcess = null
    }
  }, 3000)
}

// ─────────────────────────────────────────────────────────────────────────────

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 720,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  App Lifecycle
// ─────────────────────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.jarvis')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.on('ping', () => console.log('pong'))

  // ── Spawn the Python backend BEFORE creating the window ──────────────────
  spawnPythonBackend()

  // Give the backend a moment to bind its port, then open the UI
  setTimeout(() => {
    createWindow()
  }, 1500)

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// ── Cleanup: kill backend when the app is about to exit ──────────────────────
app.on('will-quit', (event) => {
  if (pythonProcess) {
    // Prevent the app from quitting instantly — give killBackend a chance
    event.preventDefault()
    killBackend()
    // After SIGKILL timeout (3s), the process should be dead; quit for real
    setTimeout(() => {
      if (killTimer) clearTimeout(killTimer)
      pythonProcess = null
      app.quit()
    }, 3500)
  }
})

// Quit when all windows are closed (Windows / Linux behaviour)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
