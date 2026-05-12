const dgram = require('dgram');
const vscode = require('vscode');
const fs = require('fs');
const os = require('os');
const path = require('path');

const CORDELIA_PORT = 10015;
const CORDELIA_HOST = 'localhost';
const KEYBINDING_KEY = 'cordelia.keybindingInstalled';

// ── keybindings.json helpers ──────────────────────────────────────────────────

function keybindingsPath() {
	const home = os.homedir();
	switch (process.platform) {
		case 'win32':
			return path.join(process.env.APPDATA || path.join(home, 'AppData', 'Roaming'), 'Code', 'User', 'keybindings.json');
		case 'darwin':
			return path.join(home, 'Library', 'Application Support', 'Code', 'User', 'keybindings.json');
		default:
			return path.join(home, '.config', 'Code', 'User', 'keybindings.json');
	}
}

function readKeybindings(p) {
	try {
		const raw = fs.readFileSync(p, 'utf8');
		// Strip JSONC single-line and block comments before parsing
		const stripped = raw
			.replace(/\/\/[^\n]*/g, '')
			.replace(/\/\*[\s\S]*?\*\//g, '')
			.trim();
		return stripped ? JSON.parse(stripped) : [];
	} catch {
		return [];
	}
}

function writeKeybindings(p, bindings) {
	fs.mkdirSync(path.dirname(p), { recursive: true });
	fs.writeFileSync(p, JSON.stringify(bindings, null, 2), 'utf8');
}

async function ensureKeybinding(context) {
	if (context.globalState.get(KEYBINDING_KEY)) return;

	const p = keybindingsPath();
	const bindings = readKeybindings(p);

	// Already present — nothing to do
	if (bindings.some(b => b.command === 'cordelia.sendDocument')) {
		context.globalState.update(KEYBINDING_KEY, true);
		return;
	}

	bindings.push({
		key: 'ctrl+enter',
		command: 'cordelia.sendDocument',
		when: "editorTextFocus && resourceExtname == '.cor'"
	});
	// Suppress the Csound plugin's ctrl+enter for .cor files so it doesn't
	// race with ours on port 10000.
	bindings.push({
		key: 'ctrl+enter',
		command: '-extension.csoundEvalOrc',
		when: "resourceExtname == '.cor'"
	});

	try {
		writeKeybindings(p, bindings);
		context.globalState.update(KEYBINDING_KEY, true);
		const choice = await vscode.window.showInformationMessage(
			'Cordelia: added Ctrl+Enter keybinding to your VS Code settings. Reload to activate.',
			'Reload Now'
		);
		if (choice === 'Reload Now') {
			vscode.commands.executeCommand('workbench.action.reloadWindow');
		}
	} catch (err) {
		vscode.window.showWarningMessage(`Cordelia: could not write keybindings.json — ${err.message}`);
	}
}

// ── UDP send ──────────────────────────────────────────────────────────────────

function sendToCordelia(text) {
	return new Promise((resolve, reject) => {
		const client = dgram.createSocket('udp4');
		const message = Buffer.from(text, 'utf8');
		client.send(message, CORDELIA_PORT, CORDELIA_HOST, (err) => {
			client.close();
			if (err) reject(err);
			else resolve();
		});
	});
}

// ── extension lifecycle ───────────────────────────────────────────────────────

function activate(context) {
	ensureKeybinding(context);

	const cmd = vscode.commands.registerCommand('cordelia.sendDocument', async () => {
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage('Cordelia: no active editor.');
			return;
		}

		const text = editor.document.getText();
		if (!text.trim()) {
			vscode.window.showWarningMessage('Cordelia: document is empty.');
			return;
		}

		try {
			await sendToCordelia(text);
			vscode.window.setStatusBarMessage('Cordelia: sent ✓', 2000);
		} catch (err) {
			vscode.window.showErrorMessage(`Cordelia: failed to send — ${err.message}`);
		}
	});

	context.subscriptions.push(cmd);
}

function deactivate() {}

module.exports = { activate, deactivate };
