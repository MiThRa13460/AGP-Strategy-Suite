using System;
using System.Threading;
using System.Threading.Tasks;
using AGPStrategy.Models;
using Newtonsoft.Json;
using WebSocketSharp;

namespace AGPStrategy
{
    /// <summary>
    /// Handles WebSocket connection to AGP Strategy Suite backend.
    /// </summary>
    public class DataConnector : IDisposable
    {
        private WebSocket? _webSocket;
        private readonly string _serverUrl;
        private bool _isConnected;
        private bool _isDisposed;
        private Timer? _reconnectTimer;
        private readonly object _lock = new object();

        /// <summary>
        /// Current data received from backend.
        /// </summary>
        public AGPData? CurrentData { get; private set; }

        /// <summary>
        /// Whether the connector is connected to the backend.
        /// </summary>
        public bool IsConnected => _isConnected;

        /// <summary>
        /// Event raised when data is received.
        /// </summary>
        public event EventHandler<AGPData>? DataReceived;

        /// <summary>
        /// Event raised when connection state changes.
        /// </summary>
        public event EventHandler<bool>? ConnectionStateChanged;

        /// <summary>
        /// Event raised on error.
        /// </summary>
        public event EventHandler<string>? Error;

        /// <summary>
        /// Creates a new DataConnector.
        /// </summary>
        /// <param name="host">Backend host (default: localhost)</param>
        /// <param name="port">Backend port (default: 8765)</param>
        public DataConnector(string host = "localhost", int port = 8765)
        {
            _serverUrl = $"ws://{host}:{port}";
            CurrentData = new AGPData();
        }

        /// <summary>
        /// Connect to the AGP Strategy Suite backend.
        /// </summary>
        public void Connect()
        {
            if (_isDisposed) return;

            lock (_lock)
            {
                if (_webSocket != null && _webSocket.ReadyState == WebSocketState.Open)
                {
                    return;
                }

                try
                {
                    _webSocket?.Close();
                    _webSocket = new WebSocket(_serverUrl);

                    _webSocket.OnOpen += OnWebSocketOpen;
                    _webSocket.OnMessage += OnWebSocketMessage;
                    _webSocket.OnError += OnWebSocketError;
                    _webSocket.OnClose += OnWebSocketClose;

                    _webSocket.ConnectAsync();
                }
                catch (Exception ex)
                {
                    OnError($"Connection error: {ex.Message}");
                    ScheduleReconnect();
                }
            }
        }

        /// <summary>
        /// Disconnect from the backend.
        /// </summary>
        public void Disconnect()
        {
            lock (_lock)
            {
                _reconnectTimer?.Dispose();
                _reconnectTimer = null;

                if (_webSocket != null)
                {
                    _webSocket.OnOpen -= OnWebSocketOpen;
                    _webSocket.OnMessage -= OnWebSocketMessage;
                    _webSocket.OnError -= OnWebSocketError;
                    _webSocket.OnClose -= OnWebSocketClose;

                    if (_webSocket.ReadyState == WebSocketState.Open)
                    {
                        _webSocket.Close();
                    }
                    _webSocket = null;
                }

                SetConnectionState(false);
            }
        }

        /// <summary>
        /// Send a message to the backend.
        /// </summary>
        public void Send(string message)
        {
            lock (_lock)
            {
                if (_webSocket?.ReadyState == WebSocketState.Open)
                {
                    _webSocket.Send(message);
                }
            }
        }

        /// <summary>
        /// Send a typed message to the backend.
        /// </summary>
        public void Send<T>(T data)
        {
            var json = JsonConvert.SerializeObject(data);
            Send(json);
        }

        private void OnWebSocketOpen(object? sender, EventArgs e)
        {
            SetConnectionState(true);

            // Send initial subscription message
            Send(JsonConvert.SerializeObject(new
            {
                type = "subscribe",
                channels = new[] { "telemetry", "analysis", "strategy", "recommendations", "live_timing" }
            }));
        }

        private void OnWebSocketMessage(object? sender, MessageEventArgs e)
        {
            if (string.IsNullOrEmpty(e.Data)) return;

            try
            {
                var data = JsonConvert.DeserializeObject<AGPData>(e.Data);
                if (data != null)
                {
                    CurrentData = data;
                    DataReceived?.Invoke(this, data);
                }
            }
            catch (JsonException ex)
            {
                // Try to parse as a specific message type
                try
                {
                    var message = JsonConvert.DeserializeObject<dynamic>(e.Data);
                    var type = (string?)message?.type;

                    switch (type)
                    {
                        case "telemetry":
                            if (CurrentData != null)
                            {
                                CurrentData.Telemetry = JsonConvert.DeserializeObject<TelemetryData>(
                                    JsonConvert.SerializeObject(message?.data));
                                DataReceived?.Invoke(this, CurrentData);
                            }
                            break;

                        case "analysis":
                            if (CurrentData != null)
                            {
                                CurrentData.Analysis = JsonConvert.DeserializeObject<AnalysisData>(
                                    JsonConvert.SerializeObject(message?.data));
                                DataReceived?.Invoke(this, CurrentData);
                            }
                            break;

                        case "strategy":
                            if (CurrentData != null)
                            {
                                CurrentData.Strategy = JsonConvert.DeserializeObject<StrategyData>(
                                    JsonConvert.SerializeObject(message?.data));
                                DataReceived?.Invoke(this, CurrentData);
                            }
                            break;
                    }
                }
                catch
                {
                    OnError($"Failed to parse message: {ex.Message}");
                }
            }
        }

        private void OnWebSocketError(object? sender, ErrorEventArgs e)
        {
            OnError($"WebSocket error: {e.Message}");
        }

        private void OnWebSocketClose(object? sender, CloseEventArgs e)
        {
            SetConnectionState(false);

            if (!_isDisposed && !e.WasClean)
            {
                ScheduleReconnect();
            }
        }

        private void SetConnectionState(bool connected)
        {
            if (_isConnected != connected)
            {
                _isConnected = connected;
                ConnectionStateChanged?.Invoke(this, connected);
            }
        }

        private void OnError(string message)
        {
            Error?.Invoke(this, message);
        }

        private void ScheduleReconnect()
        {
            if (_isDisposed) return;

            _reconnectTimer?.Dispose();
            _reconnectTimer = new Timer(_ =>
            {
                if (!_isDisposed)
                {
                    Connect();
                }
            }, null, TimeSpan.FromSeconds(5), Timeout.InfiniteTimeSpan);
        }

        public void Dispose()
        {
            if (_isDisposed) return;
            _isDisposed = true;

            Disconnect();
            GC.SuppressFinalize(this);
        }
    }
}
