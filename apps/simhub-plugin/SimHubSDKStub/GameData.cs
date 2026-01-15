namespace GameReaderCommon
{
    /// <summary>
    /// Game data structure passed to plugins.
    /// </summary>
    public struct GameData
    {
        /// <summary>
        /// Whether a game is currently running.
        /// </summary>
        public bool GameRunning { get; set; }

        /// <summary>
        /// Whether the game is paused.
        /// </summary>
        public bool GamePaused { get; set; }

        /// <summary>
        /// Current game name.
        /// </summary>
        public string? GameName { get; set; }

        /// <summary>
        /// Session type.
        /// </summary>
        public string? SessionType { get; set; }

        /// <summary>
        /// Current lap number.
        /// </summary>
        public int CurrentLap { get; set; }

        /// <summary>
        /// Total laps in session.
        /// </summary>
        public int TotalLaps { get; set; }

        /// <summary>
        /// Current position.
        /// </summary>
        public int Position { get; set; }

        /// <summary>
        /// Total number of cars.
        /// </summary>
        public int TotalCars { get; set; }

        /// <summary>
        /// Current fuel level.
        /// </summary>
        public double Fuel { get; set; }

        /// <summary>
        /// Maximum fuel capacity.
        /// </summary>
        public double MaxFuel { get; set; }

        /// <summary>
        /// Current speed in km/h.
        /// </summary>
        public double Speed { get; set; }

        /// <summary>
        /// Engine RPM.
        /// </summary>
        public double Rpm { get; set; }

        /// <summary>
        /// Current gear.
        /// </summary>
        public int Gear { get; set; }

        /// <summary>
        /// Throttle position (0-100).
        /// </summary>
        public double Throttle { get; set; }

        /// <summary>
        /// Brake position (0-100).
        /// </summary>
        public double Brake { get; set; }

        /// <summary>
        /// Clutch position (0-100).
        /// </summary>
        public double Clutch { get; set; }
    }
}
