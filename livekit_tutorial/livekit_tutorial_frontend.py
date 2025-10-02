// LiveKit Frontend Cheat Sheet (React/Next.js)
// A guide to building a web client that connects to a LiveKit voice agent.
// This cheat sheet focuses on the connection architecture and key code patterns.
//
// Created by Gemini based on LiveKit examples.
// Note: This file uses TypeScript/TSX syntax within comments for clarity.

// ==============================================================================
// I. The Core Connection Model: How Frontend and Backend Meet
// ==============================================================================

// This is the most critical concept to understand. The frontend (your web app)
// and the backend (the Python agent) DO NOT connect directly to each other.
// Instead, they both connect to the same LiveKit Room, which acts as a central
// meeting point and media server.

// Here's the step-by-step flow:

// 1.  **The Meeting Point:** A LiveKit Room is a virtual space identified by a unique name.
//
// 2.  **The Agent (Backend) Joins:** Your Python agent worker starts up. It uses its
//     permanent, secret **LIVEKIT_API_KEY** and **LIVEKIT_API_SECRET** to authenticate
//     with the LiveKit server and joins the specific room it's assigned to. It waits
//     there for a user.
//
// 3.  **The User (Frontend) Needs to Join:** Your React app in the user's browser
//     also needs to join that *same room*.
//
// 4.  **The Security Handshake (Token Generation):** The browser CANNOT store the
//     permanent API Key and Secret. Doing so would be a major security risk. Instead,
//     the frontend must request a temporary, short-lived **Access Token**.
//
// 5.  **The Token Endpoint:** Your frontend web server (e.g., a Next.js API route)
//     is the only place that should have the API Key and Secret. The React client makes
//     a `fetch` request to its own server's API endpoint (e.g., `/api/connection-details`).
//     This endpoint uses the `livekit-server-sdk` to generate a temporary token that grants
//     the user access to a specific room for a limited time.
//
// 6.  **Connection:** The React client receives the token and the LiveKit server URL.
//     It uses these details to connect to the LiveKit Room.
//
// 7.  **Interaction:** Now, both the user and the agent are "participants" in the same room.
//     - The user's microphone audio is published to the room.
//     - The agent automatically subscribes to that audio.
//     - The agent processes the audio, thinks, and publishes its own speech audio back to the room.
//     - The user's browser subscribes to the agent's audio and plays it through the speakers.

// 

// ==============================================================================
// II. Frontend Implementation (React & Next.js)
// ==============================================================================

// Let's look at the code that makes this happen.

// 2.1: Environment Setup (`.env.local`)
// ------------------------------------
// # Your Next.js project's root will have a `.env.local` file. This file holds
// # the secrets for your *web server*, NOT the browser.

/* .env.local */
// These are used by the server-side Token Endpoint.
LIVEKIT_API_KEY=<your_api_key>
LIVEKIT_API_SECRET=<your_api_secret>

// This is used by both the server-side endpoint and the client-side code.
// The `NEXT_PUBLIC_` prefix makes it available in the browser.
NEXT_PUBLIC_LIVEKIT_URL=wss://<your-project>.livekit.cloud

// 2.2: The Token Endpoint (Server-Side Logic)
// -------------------------------------------
// # This is a server-side API route in your Next.js app. Its only job is to
// # securely generate a temporary access token for the client.

/* app/api/connection-details/route.ts */
import { NextResponse } from 'next/server';
import { AccessToken, type VideoGrant } from 'livekit-server-sdk';

// Get secrets from environment variables (only accessible on the server)
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL;

export async function GET() {
  // This endpoint creates a unique room and identity for each new session.
  const roomName = `voice-agent-room-${Math.floor(Math.random() * 1000)}`;
  const participantIdentity = `user-${Math.floor(Math.random() * 1000)}`;

  if (!API_KEY || !API_SECRET) {
    throw new Error('LiveKit API credentials are not set.');
  }

  // Create a new AccessToken
  const at = new AccessToken(API_KEY, API_SECRET, {
    identity: participantIdentity,
    ttl: '15m', // The token is valid for 15 minutes
  });

  // Define the permissions for the user
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  const token = await at.toJwt();

  // Send the token and connection details back to the client
  return NextResponse.json({
    serverUrl: LIVEKIT_URL,
    roomName: roomName,
    participantToken: token,
  });
}

// 2.3: Connecting from the Client (React Component)
// -------------------------------------------------
// # The React component uses a hook to fetch the connection details from the token
// # endpoint and then uses the LiveKit Components SDK to connect to the room.

/* components/app.tsx */
import { useEffect, useMemo, useState } from 'react';
import { Room } from 'livekit-client';
import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';

export function App() {
  const [serverUrl, setServerUrl] = useState('');
  const [token, setToken] = useState('');

  const connectToRoom = async () => {
    // 1. Fetch connection details from our own API endpoint.
    const res = await fetch('/api/connection-details');
    const data = await res.json();
    
    // 2. Set the state with the received URL and token.
    setServerUrl(data.serverUrl);
    setToken(data.participantToken);
  };

  return (
    <div>
      {token ? (
        // 3. Once we have a token, the LiveKitRoom component handles the connection.
        <LiveKitRoom
          serverUrl={serverUrl}
          token={token}
          audio={true}
          video={true} // Enable video if your agent uses it
          data-lk-theme="default"
        >
          {/* Your main app UI goes here */}
          <MyVoiceAgentUI />
          {/* This component ensures you can hear the agent */}
          <RoomAudioRenderer />
        </LiveKitRoom>
      ) : (
        // 4. Before connecting, show a "Start" button.
        <button onClick={connectToRoom}>Start Call</button>
      )}
    </div>
  );
}


// ==============================================================================
// III. Interacting with the Agent
// ==============================================================================

// 3.1: Handling Audio and Video
// -----------------------------
// # The `@livekit/components-react` package makes handling media streams easy.
// # The `<RoomAudioRenderer />` automatically plays audio from all participants,
// # including the agent. Hooks like `useVoiceAssistant` provide the agent's state
// # and audio track for building custom UI, like a voice visualizer.

/* components/MyVoiceAgentUI.tsx */
import { useVoiceAssistant, BarVisualizer } from "@livekit/components-react";

function MyVoiceAgentUI() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div>
      <p>Agent is currently: {state}</p>
      <BarVisualizer
        state={state}
        trackRef={audioTrack}
        style={{ width: '100%', height: '100px' }}
      />
    </div>
  );
}

// 3.2: RPC (Remote Procedure Call) for Data Exchange
// --------------------------------------------------
// # While audio flows automatically, you often need to send structured data
// # between the agent and the frontend (e.g., to update a UI with notes,
// # display a thinking indicator, or send a command). This is done with RPC.

/* components/MedicalNotes.tsx */
import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';

export function MedicalNotes() {
  const [notes, setNotes] = useState('');
  const room = useRoomContext();

  useEffect(() => {
    if (!room || !room.localParticipant) return;

    // 1. Define the handler function for an incoming RPC from the agent.
    const handleReceiveNotes = async (rpcInvocation: any): Promise<string> => {
      const payload = JSON.parse(rpcInvocation.payload);
      if (payload && payload.notes) {
        setNotes(payload.notes); // Update the React state with the new notes
      }
      return 'Success: Notes received';
    };

    // 2. Register the RPC method on the local participant (the user).
    //    The agent can now call the "receive_notes" method on this user.
    room.localParticipant.registerRpcMethod('receive_notes', handleReceiveNotes);

    return () => {
      // Clean up by unregistering the method
      room.localParticipant.unregisterRpcMethod('receive_notes');
    };
  }, [room]);

  return <div>{notes}</div>;
}


// ==============================================================================
// IV. Backend Prerequisite: Downloading Model Files
// ==============================================================================

// You are correct to point out the `download-files` step. This is a critical
// **backend setup task** that must be completed before the Python agent can run.
// It is *not* a frontend concern, but the frontend won't have an agent to talk
// to if this step is missed.

// **What is it for?**
// LiveKit agent plugins for tasks like Voice Activity Detection (VAD) or Turn Detection
// rely on pre-trained machine learning models. These model files are not included
// directly in the Python package to keep it lightweight.

// **The `download-files` Command:**
// A well-structured agent project will provide a helper script or command to download
// these necessary files. This command typically does the following:
// 1.  Checks for the existence of model files in a local cache directory.
// 2.  If they are missing, it downloads them from a model hosting service (like Hugging Face).

// **How to Run It (Based on your example):**
// The `README.md` you provided shows a common and effective pattern using `make` or `uv`.
// This command needs to be run in the **backend project's terminal**, not the frontend.

/* In your backend (Python agent) terminal: */

// Using a Makefile for convenience
// make download-files

// Or running the command directly via the Python module
// uv run -m src.livekit.agent download-files

// **Why is this necessary?**
// Without these files, the agent will fail to start, often with a `FileNotFoundError`.
// For example, when the code `silero.VAD.load()` is executed, it expects the
// Silero VAD model file to be present locally. The `download-files` command
// ensures it is.

// **Key Takeaway:**
// The `download-files` command is a **one-time setup step for the backend agent**.
// It ensures the agent has all the local ML models it needs to function before it
// tries to connect to a LiveKit room.




// ==============================================================================
// V. Cloud Deployment
// ==============================================================================

// The connection architecture remains the same in the cloud. You just deploy
// the different pieces to different services.

// 1.  **LiveKit Server:** The easiest way is to use **LiveKit Cloud**. It gives you a
//     server URL and API credentials without needing to manage servers yourself.
//
// 2.  **Frontend (React/Next.js App):** Deploy this to a static web hosting service
//     like **Vercel** or **Netlify**. These platforms are perfect for Next.js and
//     will handle both the client-side React code and the server-side token endpoint.
//
// 3.  **Agent (Python Backend):** The agent is a long-running process. It should be
//     packaged in a **Docker container** and deployed to a service that can run
//     containers, such as:
//     - **Google Cloud Run**
//     - **AWS Fargate**
//     - A standard Virtual Machine (e.g., Google Compute Engine, AWS EC2)
//
// All three components will communicate over the internet. You just need to ensure
// your environment variables (e.g., `NEXT_PUBLIC_LIVEKIT_URL`, `LIVEKIT_API_KEY`)
// are set correctly in each respective deployment environment.