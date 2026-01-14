// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod overlay;

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_updater::UpdaterExt;

use overlay::{
    apply_overlay_preset, close_overlay, create_overlay, get_overlay_configs, get_overlay_presets,
    save_overlay_preset, set_overlay_click_through, toggle_all_overlays, toggle_overlay,
    update_overlay_config, OverlayState,
};

struct PythonProcess(Mutex<Option<Child>>);

#[tauri::command]
fn start_backend() -> Result<String, String> {
    // TODO: Start Python backend as sidecar
    Ok("Backend started".to_string())
}

#[tauri::command]
fn stop_backend(state: tauri::State<PythonProcess>) -> Result<String, String> {
    let mut process = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = process.take() {
        child.kill().map_err(|e| e.to_string())?;
        return Ok("Backend stopped".to_string());
    }
    Ok("Backend was not running".to_string())
}

#[tauri::command]
fn get_current_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .manage(PythonProcess(Mutex::new(None)))
        .manage(OverlayState::default())
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            get_current_version,
            // Overlay commands
            create_overlay,
            close_overlay,
            toggle_overlay,
            toggle_all_overlays,
            update_overlay_config,
            get_overlay_configs,
            get_overlay_presets,
            apply_overlay_preset,
            save_overlay_preset,
            set_overlay_click_through,
        ])
        .setup(|app| {
            // Open devtools in debug mode
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }

            // Register global hotkeys
            // F1 = Toggle all overlays
            // F2 = Toggle telemetry overlay
            // F3 = Toggle strategy overlay
            // F4 = Toggle standings overlay

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
