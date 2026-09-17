/**
 * ORNITHOPTER — App de Controlo (Expo / React Native)
 *
 * Telemóvel → HTTP/WebSocket → Raspberry Pi (estação de solo) → UDP → drone.
 * A RPi é a única que fala com o drone; a app é o painel remoto.
 *
 * Ecrãs: Ligação · Joystick · Telemetria · Segurança (EMERGENCY sempre visível).
 */
import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View, TextInput, Pressable, ScrollView } from "react-native";
import { StatusBar } from "expo-status-bar";

// TODO(n13): definir IP fixo da RPi na rede da escola ou descoberta mDNS
const DEFAULT_HOST = "192.168.1.50:8000";

type Telemetry = {
  mode: string;
  x: number; y: number; z: number;
  yaw: number; roll: number; pitch: number;
  battery: number;
  markerLost: boolean;
};

async function cmd(host: string, path: string, body?: object) {
  try {
    const res = await fetch(`http://${host}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    return await res.json();
  } catch {
    return { error: "sem ligação à estação de solo" };
  }
}

export default function App() {
  const [host, setHost] = useState(DEFAULT_HOST);
  const [connected, setConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!connected) return;
    const ws = new WebSocket(`ws://${host}/ws/telemetry`);
    ws.onmessage = (e) => {
      try { setTelemetry(JSON.parse(e.data)); } catch {}
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [connected, host]);

  const send = (path: string, body?: object) => cmd(host, path, body);

  return (
    <View style={s.root}>
      <StatusBar style="light" />
      <Text style={s.title}>ORNITHOPTER</Text>
      <Text style={s.sub}>estação de solo · Raspberry Pi</Text>

      {!connected ? (
        <View style={s.card}>
          <Text style={s.label}>IP da estação de solo</Text>
          <TextInput style={s.input} value={host} onChangeText={setHost} autoCapitalize="none" />
          <Pressable style={s.btn} onPress={() => setConnected(true)}>
            <Text style={s.btnText}>LIGAR</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView contentContainerStyle={s.card}>
          <View style={s.telem}>
            <Text style={s.telemLine}>
              modo: {telemetry?.mode ?? "…"}   marcador: {telemetry?.markerLost ? "PERDIDO ⚠" : "OK ✓"}
            </Text>
            <Text style={s.telemLine}>
              pos: {telemetry?.x.toFixed(0)}, {telemetry?.y.toFixed(0)}, {telemetry?.z.toFixed(0)} mm
            </Text>
            <Text style={s.telemLine}>
              atitude: r {telemetry?.roll.toFixed(1)}° p {telemetry?.pitch.toFixed(1)}° y {telemetry?.yaw.toFixed(1)}°
            </Text>
            <Text style={[s.telemLine, (telemetry?.battery ?? 4) < 3.4 && { color: "#e03131" }]}>
              bateria: {telemetry?.battery.toFixed(2)} V
            </Text>
          </View>

          <Pressable style={s.btn} onPress={() => send("/takeoff")}>
            <Text style={s.btnText}>DECOLAR (50 cm)</Text>
          </Pressable>
          <Pressable style={s.btn} onPress={() => send("/land")}>
            <Text style={s.btnText}>ATERRAR</Text>
          </Pressable>
          {/* TODO(n13): joystick virtual — 2 pan gestures → /goto x,y */}

          <Pressable style={s.btnDanger} onPress={() => send("/emergency")}>
            <Text style={s.btnText}>⬛ EMERGENCY — MOTORES OFF</Text>
          </Pressable>
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#14100b", alignItems: "center", paddingTop: 60 },
  title: { color: "#e8a765", fontSize: 28, letterSpacing: 8 },
  sub: { color: "#a89880", marginTop: 4, marginBottom: 30, letterSpacing: 2 },
  card: { width: "88%", gap: 12 },
  label: { color: "#a89880", fontSize: 12, letterSpacing: 1 },
  input: { backgroundColor: "#1e1810", color: "#e8dcc8", borderColor: "#3a2f22", borderWidth: 1, borderRadius: 8, padding: 12 },
  btn: { backgroundColor: "#ff7b24", borderRadius: 8, padding: 16, alignItems: "center" },
  btnDanger: { backgroundColor: "#c43d3d", borderRadius: 8, padding: 16, alignItems: "center", marginTop: 20 },
  btnText: { color: "#14100b", fontWeight: "800", letterSpacing: 1 },
  telem: { backgroundColor: "#1e1810", borderColor: "#3a2f22", borderWidth: 1, borderRadius: 8, padding: 14, marginBottom: 10 },
  telemLine: { color: "#e8dcc8", fontFamily: "monospace", fontSize: 13, lineHeight: 22 },
});
