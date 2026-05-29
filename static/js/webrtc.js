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

    const peer = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });

    let localStream;
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localVideo.srcObject = localStream;
        localStream.getTracks().forEach((track) => peer.addTrack(track, localStream));
    } catch (_error) {
        showToast("Camera or microphone permission is required for consultation.", "danger");
        return;
    }

    peer.ontrack = (event) => {
        remoteVideo.srcObject = event.streams[0];
    };

    peer.onicecandidate = (event) => {
        if (event.candidate) socket.emit("webrtc_signal", { appointment_id: appointmentId, candidate: event.candidate });
    };

    socket.emit("join", { appointment_id: appointmentId });

    socket.on("webrtc_signal", async (data) => {
        if (data.offer) {
            await peer.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            socket.emit("webrtc_signal", { appointment_id: appointmentId, answer });
        }
        if (data.answer) await peer.setRemoteDescription(new RTCSessionDescription(data.answer));
        if (data.candidate) await peer.addIceCandidate(new RTCIceCandidate(data.candidate));
    });

    setTimeout(async () => {
        if (!peer.localDescription) {
            const offer = await peer.createOffer();
            await peer.setLocalDescription(offer);
            socket.emit("webrtc_signal", { appointment_id: appointmentId, offer });
        }
    }, 1200);

    muteBtn?.addEventListener("click", () => {
        localStream.getAudioTracks().forEach((track) => track.enabled = !track.enabled);
        showToast(localStream.getAudioTracks()[0]?.enabled ? "Microphone on." : "Microphone muted.");
    });

    videoBtn?.addEventListener("click", () => {
        localStream.getVideoTracks().forEach((track) => track.enabled = !track.enabled);
        showToast(localStream.getVideoTracks()[0]?.enabled ? "Camera on." : "Camera off.");
    });

    endBtn?.addEventListener("click", () => {
        localStream.getTracks().forEach((track) => track.stop());
        peer.close();
        showToast("Call ended.");
        setTimeout(() => history.back(), 900);
    });
});
