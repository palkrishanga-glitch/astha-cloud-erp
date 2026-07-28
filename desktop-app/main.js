const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let flaskProcess;

function startFlaskBackend() {
    const pythonExec = process.platform === 'win32' ? 'python' : 'python3';
    const scriptPath = path.join(__dirname, '..', 'backend', 'app.py');
    
    flaskProcess = spawn(pythonExec, [scriptPath]);

    flaskProcess.stdout.on('data', (data) => {
        console.log(`[Backend stdout]: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`[Backend stderr]: ${data}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        minWidth: 1024,
        minHeight: 650,
        title: "ASTHA ERP Enterprise — Astha Builders & Hardware",
        backgroundColor: '#0F172A',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'index.html'));

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', () => {
    startFlaskBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (flaskProcess) flaskProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
    if (flaskProcess) flaskProcess.kill();
});
