document.addEventListener("DOMContentLoaded", async () => {
    const room = document.querySelector(".video-room");

    if (!room || !window.io) return;

    const appointmentId = room.dataset.appointmentId;
    const socket = io();

    const localVideo = document.querySelector("#localVideo");
    const remoteVideo = document.querySelector("#remoteVideo");
    const muteBtn = document.querySelector("#muteBtn");
    const videoBtn = document.querySelector("#videoBtn");
    const endBtn = document.querySelector("#endBtn");

    let localStream = null;
    let peer = null;
    let makingOffer = false;
    let remoteDescriptionSet = false;

    const isDoctor = window.location.pathname.includes("/doctor/");
    const polite = !isDoctor;

    async function startMedia() {
        try {
            localStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true,
            });

            localVideo.srcObject = localStream;
            return true;
        } catch (error) {
            console.error("Media permission error:", error);

            showToast(
                "Camera and microphone permission is required. Use HTTPS or localhost.",
                "danger"
            );

            return false;
        }
    }

    function createPeerConnection() {
        peer = new RTCPeerConnection({
            iceServers: [
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" },
            ],
        });

        localStream.getTracks().forEach((track) => {
            peer.addTrack(track, localStream);
        });

        peer.ontrack = (event) => {
            console.log("Remote stream received");

            if (remoteVideo.srcObject !== event.streams[0]) {
                remoteVideo.srcObject = event.streams[0];
            }
        };

        peer.onicecandidate = (event) => {
            if (event.candidate) {
                socket.emit("webrtc_signal", {
                    appointment_id: appointmentId,
                    candidate: event.candidate,
                });
            }
        };

        peer.onconnectionstatechange = () => {
            console.log("Connection state:", peer.connectionState);

            if (peer.connectionState === "connected") {
                showToast("Video consultation connected.");
            }

            if (
                peer.connectionState === "failed" ||
                peer.connectionState === "disconnected"
            ) {
                showToast(
                    "Connection interrupted. Rejoin the room if needed.",
                    "warning"
                );
            }
        };

        peer.onnegotiationneeded = async () => {
            try {
                makingOffer = true;

                await peer.setLocalDescription();

                socket.emit("webrtc_signal", {
                    appointment_id: appointmentId,
                    description: peer.localDescription,
                });
            } catch (error) {
                console.error("Negotiation error:", error);
            } finally {
                makingOffer = false;
            }
        };
    }

    socket.on("connect", async () => {
        console.log("Socket connected");

        const mediaStarted = await startMedia();

        if (!mediaStarted) return;

        createPeerConnection();

        socket.emit("join", {
            appointment_id: appointmentId,
        });

        socket.emit("ready_for_call", {
            appointment_id: appointmentId,
        });
    });

    socket.on("peer_joined", (data) => {
        console.log("Peer joined:", data);
        showToast(`${data.role || "Peer"} joined the consultation.`);
    });

    socket.on("ready_for_call", async () => {
        console.log("Peer ready for call");

        if (!peer) return;

        try {
            if (isDoctor) {
                await peer.setLocalDescription();

                socket.emit("webrtc_signal", {
                    appointment_id: appointmentId,
                    description: peer.localDescription,
                });
            }
        } catch (error) {
            console.error("Ready call offer error:", error);
        }
    });

    socket.on("webrtc_signal", async (data) => {
        if (!peer) return;

        try {
            if (data.description) {
                const description = data.description;

                const offerCollision =
                    description.type === "offer" &&
                    (makingOffer || peer.signalingState !== "stable");

                const ignoreOffer = !polite && offerCollision;

                if (ignoreOffer) {
                    console.log("Ignoring offer collision");
                    return;
                }

                await peer.setRemoteDescription(description);
                remoteDescriptionSet = true;

                if (description.type === "offer") {
                    await peer.setLocalDescription();

                    socket.emit("webrtc_signal", {
                        appointment_id: appointmentId,
                        description: peer.localDescription,
                    });
                }
            }

            if (data.candidate) {
                if (remoteDescriptionSet || peer.remoteDescription) {
                    await peer.addIceCandidate(data.candidate);
                }
            }
        } catch (error) {
            console.error("WebRTC signal error:", error);
        }
    });

    socket.on("peer_left", () => {
        showToast("The other participant left the consultation.", "warning");
        remoteVideo.srcObject = null;
    });

    muteBtn?.addEventListener("click", () => {
        if (!localStream) return;

        localStream.getAudioTracks().forEach((track) => {
            track.enabled = !track.enabled;
        });

        const enabled = localStream.getAudioTracks()[0]?.enabled;

        showToast(enabled ? "Microphone on." : "Microphone muted.");
    });

    videoBtn?.addEventListener("click", () => {
        if (!localStream) return;

        localStream.getVideoTracks().forEach((track) => {
            track.enabled = !track.enabled;
        });

        const enabled = localStream.getVideoTracks()[0]?.enabled;

        showToast(enabled ? "Camera on." : "Camera off.");
    });

    endBtn?.addEventListener("click", () => {
        socket.emit("leave_call", {
            appointment_id: appointmentId,
        });

        if (localStream) {
            localStream.getTracks().forEach((track) => track.stop());
        }

        if (peer) {
            peer.close();
        }

        showToast("Call ended.");

        setTimeout(() => {
            history.back();
        }, 800);
    });
});