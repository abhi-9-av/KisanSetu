# KisanSetu mobile app

This is the Expo Router farmer-facing frontend. It uses NativeWind for the
Tailwind CSS styling used by `app/index.tsx`.

## Run locally

From this directory:

```bash
npm install
npm start
```

Use the Expo Go QR code, or run `npm run ios`, `npm run android`, or
`npm run web`.

## Checks

```bash
npm run typecheck
```
# Mobile app

Run `npm run typecheck` to validate TypeScript. The app talks to the local
FastAPI server by default (`http://localhost:8000` on iOS/web and
`http://10.0.2.2:8000` on the Android emulator). For a physical device, set
the LAN address before starting Expo:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.20:8000 npx expo start
```

The development login uses OTP `1234`; it is an in-memory development flow and
does not send SMS. If the backend is unavailable, the existing demo UI remains
available in the source as a fallback for design work.
