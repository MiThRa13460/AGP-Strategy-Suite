"""
AGP Strategy Suite - WebSocket Server
Broadcasts telemetry and setup recommendations to frontend
"""

import asyncio
import json
import time
from typing import Set

import websockets

from agp_core.telemetry.rf2_shared_memory import RF2SharedMemory
from agp_core.analysis.setup_analyzer import SetupAnalyzer


class AGPServer:
    """Main WebSocket server for AGP Strategy Suite"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.rf2 = RF2SharedMemory()
        self.analyzer = SetupAnalyzer()
        self.running = False
        self.update_rate = 60  # Hz

    async def register(self, websocket):
        """Register new client"""
        self.clients.add(websocket)
        print(f"[AGP] Client connected. Total: {len(self.clients)}")

        await websocket.send(json.dumps({
            "type": "status",
            "connected": self.rf2.connected,
            "message": "Connected to AGP Strategy Suite",
            "version": "0.1.0"
        }))

    async def unregister(self, websocket):
        """Unregister client"""
        self.clients.discard(websocket)
        print(f"[AGP] Client disconnected. Total: {len(self.clients)}")

    async def broadcast(self, message: str):
        """Broadcast message to all clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

    async def handle_client(self, websocket, path=None):
        """Handle client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def handle_message(self, websocket, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "get_status":
                await websocket.send(json.dumps({
                    "type": "status",
                    "connected": self.rf2.connected,
                    "clients": len(self.clients)
                }))

            elif msg_type == "get_recommendations":
                recs = self.analyzer.generate_recommendations()
                await websocket.send(json.dumps({
                    "type": "recommendations",
                    "data": [
                        {
                            "parameter": r.parameter,
                            "direction": r.direction,
                            "value": r.value,
                            "reason": r.reason,
                            "priority": r.priority,
                            "side_effects": r.side_effects,
                            "confidence": r.confidence
                        }
                        for r in recs
                    ]
                }))

            elif msg_type == "get_summary":
                summary = self.analyzer.get_summary()
                await websocket.send(json.dumps({
                    "type": "summary",
                    "data": summary
                }))

            elif msg_type == "load_setup":
                path = data.get("path")
                if path:
                    success = self.analyzer.load_setup(path)
                    await websocket.send(json.dumps({
                        "type": "setup_loaded",
                        "success": success
                    }))

            elif msg_type == "ping":
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": time.time()
                }))

        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def telemetry_loop(self):
        """Main telemetry reading and broadcasting loop"""
        reconnect_delay = 1
        last_broadcast = 0
        broadcast_interval = 1 / self.update_rate

        while self.running:
            try:
                # Try to connect if not connected
                if not self.rf2.connected:
                    if self.rf2.connect():
                        print("[AGP] Connected to rFactor 2")
                        await self.broadcast(json.dumps({
                            "type": "rf2_connected",
                            "connected": True
                        }))
                        reconnect_delay = 1
                    else:
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 2, 10)
                        continue

                # Read all data
                data = self.rf2.read_all()

                if data['telemetry']:
                    # Feed analyzer
                    self.analyzer.add_sample(data['telemetry'], data['player_scoring'])

                    # Broadcast at configured rate
                    now = time.time()
                    if now - last_broadcast >= broadcast_interval:
                        last_broadcast = now

                        # Prepare broadcast data
                        t = data['telemetry']
                        s = data['scoring']
                        p = data['player_scoring']

                        broadcast_data = {
                            "type": "telemetry",
                            "timestamp": data['timestamp'],

                            # Basic
                            "vehicle": t.vehicle_name,
                            "track": t.track_name,

                            # Speed & Engine
                            "speed": round(t.speed_kmh, 1),
                            "rpm": round(t.rpm),
                            "rpm_max": round(t.rpm_max),
                            "gear": t.gear,
                            "fuel": round(t.fuel, 1),
                            "fuel_pct": round(t.fuel_pct, 1),

                            # Inputs
                            "throttle": round(t.throttle * 100, 1),
                            "brake": round(t.brake * 100, 1),
                            "steering": round(t.steering * 100, 1),
                            "clutch": round(t.clutch * 100, 1),

                            # G-Forces
                            "g_lat": round(t.g_lat, 2),
                            "g_long": round(t.g_long, 2),

                            # Tires
                            "tire_temp": {
                                "FL": round(t.tire_temp_fl, 1),
                                "FR": round(t.tire_temp_fr, 1),
                                "RL": round(t.tire_temp_rl, 1),
                                "RR": round(t.tire_temp_rr, 1)
                            },
                            "tire_pressure": {
                                "FL": round(t.tire_pressure_fl, 1),
                                "FR": round(t.tire_pressure_fr, 1),
                                "RL": round(t.tire_pressure_rl, 1),
                                "RR": round(t.tire_pressure_rr, 1)
                            },
                            "tire_wear": {
                                "FL": round(t.tire_wear_fl * 100, 1),
                                "FR": round(t.tire_wear_fr * 100, 1),
                                "RL": round(t.tire_wear_rl * 100, 1),
                                "RR": round(t.tire_wear_rr * 100, 1)
                            },
                            "grip": {
                                "FL": round(t.grip_fl * 100, 1),
                                "FR": round(t.grip_fr * 100, 1),
                                "RL": round(t.grip_rl * 100, 1),
                                "RR": round(t.grip_rr * 100, 1)
                            },

                            # Brakes
                            "brake_temp": {
                                "FL": round(t.brake_temp_fl, 1),
                                "FR": round(t.brake_temp_fr, 1),
                                "RL": round(t.brake_temp_rl, 1),
                                "RR": round(t.brake_temp_rr, 1)
                            },

                            # Aero & Chassis
                            "ride_height_front": round(t.front_ride_height, 1),
                            "ride_height_rear": round(t.rear_ride_height, 1),
                            "rake": round(t.rake, 1),
                            "front_downforce": round(t.front_downforce, 1),
                            "rear_downforce": round(t.rear_downforce, 1),

                            # Engine temps
                            "water_temp": round(t.water_temp, 1),
                            "oil_temp": round(t.oil_temp, 1),

                            # Lap
                            "lap_number": t.lap_number,
                            "sector": t.current_sector,

                            # Position
                            "pos_x": round(t.pos_x, 1),
                            "pos_y": round(t.pos_y, 1),
                            "pos_z": round(t.pos_z, 1),
                        }

                        # Add scoring data if available
                        if s:
                            broadcast_data["session"] = {
                                "track_temp": round(s.track_temp, 1),
                                "ambient_temp": round(s.ambient_temp, 1),
                                "rain": round(s.raining, 2),
                                "wetness": round(s.avg_path_wetness, 2),
                                "session_type": s.session_type,
                                "game_phase": s.game_phase
                            }

                        if p:
                            broadcast_data["position"] = {
                                "place": p.place,
                                "total_laps": p.total_laps,
                                "best_lap": round(p.best_lap_time, 3) if p.best_lap_time > 0 else None,
                                "last_lap": round(p.last_lap_time, 3) if p.last_lap_time > 0 else None,
                                "time_behind_leader": round(p.time_behind_leader, 3),
                                "time_behind_next": round(p.time_behind_next, 3),
                                "in_pits": p.in_pits,
                                "pitstops": p.num_pitstops
                            }

                        # Add analysis summary
                        summary = self.analyzer.get_summary()
                        if summary.get("status") == "ready":
                            broadcast_data["analysis"] = summary

                        await self.broadcast(json.dumps(broadcast_data))

                else:
                    await asyncio.sleep(0.1)

                await asyncio.sleep(0.001)

            except Exception as e:
                print(f"[AGP] Error in telemetry loop: {e}")
                self.rf2.disconnect()
                await asyncio.sleep(1)

    async def start(self):
        """Start the server"""
        self.running = True

        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )

        print(f"[AGP] Server started on ws://{self.host}:{self.port}")
        print("[AGP] Waiting for rFactor 2...")

        telemetry_task = asyncio.create_task(self.telemetry_loop())

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            self.rf2.disconnect()
            server.close()
            await server.wait_closed()
            telemetry_task.cancel()

    def stop(self):
        """Stop the server"""
        self.running = False


async def main():
    """Main entry point"""
    server = AGPServer(host="0.0.0.0", port=8765)

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n[AGP] Shutting down...")
        server.stop()


if __name__ == "__main__":
    print("=" * 50)
    print("AGP Strategy Suite - Python Backend")
    print("=" * 50)
    asyncio.run(main())
