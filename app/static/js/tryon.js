/**
 * OptiStyle Pro - Calibrated Optical Computer Vision AR Engine
 * High-Precision Metric Distance Normalization & Interactive 50-60cm Calibration Oval
 */

class OptiTryOnEngine {
    constructor(videoElement, canvasElement, options = {}) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = canvasElement.getContext('2d');

        this.options = {
            glassesOverlayUrl: options.glassesOverlayUrl || '/static/img/frames/square_black.svg',
            showLandmarks: false,
            showCalibrationGuide: true,
            isMirrored: true,
            onFaceAnalyzed: null,
            onNoFaceDetected: null,
            onFaceLost: null,
            onStatusChanged: null,
            onDistanceChanged: null,
            ...options
        };

        this.stream = null;
        this.glassesImage = new Image();
        this.isGlassesLoaded = false;
        
        this.isRunning = false;
        this.isPostingFrame = false;
        this.currentSource = 'idle'; // 'camera', 'image', 'idle'
        this.staticImage = null;
        
        // Active Face Position State (Interpolated)
        this.targetBox = null;
        this.currentBox = null;
        this.currentLandmarks = [];
        this.hasValidFace = false;
        this.lastTrackTime = 0;
        this.currentDistanceData = {
            distance_cm: 55,
            status: 'OPTIMAL',
            advice: 'Khoảng cách chuẩn 55 cm ✅'
        };

        this.loadGlasses(this.options.glassesOverlayUrl);
    }

    notifyStatus(statusText, type = 'info') {
        if (this.options.onStatusChanged) {
            this.options.onStatusChanged(statusText, type);
        }
    }

    loadGlasses(url) {
        this.isGlassesLoaded = false;
        this.options.glassesOverlayUrl = url;
        this.glassesImage.crossOrigin = "anonymous";
        this.glassesImage.onload = () => {
            this.isGlassesLoaded = true;
            if (this.currentSource === 'image' && this.staticImage) {
                this.renderStaticFrame();
            }
        };
        this.glassesImage.src = url;
    }

    async startCamera() {
        this.targetBox = null;
        this.currentBox = null;
        this.hasValidFace = false;

        try {
            this.notifyStatus('Đang mở camera...', 'loading');

            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: "user"
                },
                audio: false
            });

            this.video.srcObject = this.stream;

            await new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    this.canvas.width = this.video.videoWidth || 640;
                    this.canvas.height = this.video.videoHeight || 480;
                    resolve();
                };
            });

            this.isRunning = true;
            this.currentSource = 'camera';
            this.notifyStatus('Camera trực tiếp (60 FPS)', 'active');
            
            // Continuous 60 FPS Render Loop
            this.renderLiveCameraLoop();
            // Continuous Face Tracking Dispatcher
            this.runLiveFaceTracker();

            return true;
        } catch (err) {
            this.notifyStatus('Chưa cấp quyền camera', 'error');
            throw err;
        }
    }

    // 1. Live 60 FPS Canvas Renderer with Calibration Oval & Smooth Box Interpolation
    renderLiveCameraLoop() {
        if (!this.isRunning || this.currentSource !== 'camera') return;

        const width = this.canvas.width;
        const height = this.canvas.height;

        this.ctx.save();
        this.ctx.clearRect(0, 0, width, height);

        // 1. Mirror video stream
        if (this.options.isMirrored) {
            this.ctx.translate(width, 0);
            this.ctx.scale(-1, 1);
        }

        // 2. Draw live video feed
        if (this.video.readyState >= 2) {
            this.ctx.drawImage(this.video, 0, 0, width, height);
        }

        // 3. Smooth Box Interpolation (Lerp)
        if (this.targetBox && this.hasValidFace) {
            if (!this.currentBox) {
                this.currentBox = { ...this.targetBox };
            } else {
                const factor = 0.35;
                this.currentBox.center_x += (this.targetBox.center_x - this.currentBox.center_x) * factor;
                this.currentBox.center_y += (this.targetBox.center_y - this.currentBox.center_y) * factor;
                this.currentBox.width += (this.targetBox.width - this.currentBox.width) * factor;
                this.currentBox.height += (this.targetBox.height - this.currentBox.height) * factor;
                this.currentBox.angle += (this.targetBox.angle - this.currentBox.angle) * factor;
            }

            // Draw Eye Landmark Dots
            if (this.options.showLandmarks && this.currentLandmarks.length > 0) {
                this.ctx.fillStyle = "rgba(245, 158, 11, 0.85)";
                for (const pt of this.currentLandmarks) {
                    this.ctx.beginPath();
                    this.ctx.arc(pt.x, pt.y, 4, 0, 2 * Math.PI);
                    this.ctx.fill();
                }
            }

            // Draw Glasses Overlay
            if (this.isGlassesLoaded) {
                this.ctx.save();
                this.ctx.translate(this.currentBox.center_x, this.currentBox.center_y);
                this.ctx.rotate(this.currentBox.angle || 0);
                this.ctx.drawImage(
                    this.glassesImage,
                    -this.currentBox.width / 2,
                    -this.currentBox.height / 2,
                    this.currentBox.width,
                    this.currentBox.height
                );
                this.ctx.restore();
            }
        }

        this.ctx.restore();

        // 4. Draw Interactive 50-60cm Calibration Oval on top (Non-mirrored UI layer)
        if (this.options.showCalibrationGuide) {
            this.drawCalibrationOval(width, height);
        }

        requestAnimationFrame(() => this.renderLiveCameraLoop());
    }

    // Draw Optical Calibration Target Oval Guide (50-60cm Guide)
    drawCalibrationOval(width, height) {
        const centerX = width / 2;
        const centerY = height * 0.44;
        const radiusX = width * 0.23;
        const radiusY = height * 0.36;

        this.ctx.save();
        this.ctx.lineWidth = 2.5;

        let strokeColor = "rgba(245, 158, 11, 0.4)"; // default amber
        let label = "🎯 Đặt khuôn mặt vào khung chuẩn 50 - 60 cm";

        if (this.hasValidFace) {
            if (this.currentDistanceData.status === 'OPTIMAL') {
                strokeColor = "rgba(16, 185, 129, 0.85)"; // Emerald Green
                label = `✅ Khoảng cách chuẩn: ${this.currentDistanceData.distance_cm} cm (Đang đo chính xác)`;
            } else if (this.currentDistanceData.status === 'TOO_CLOSE') {
                strokeColor = "rgba(244, 63, 94, 0.85)"; // Rose Red
                label = `⚠️ Quá gần camera (${this.currentDistanceData.distance_cm} cm) - Vui lòng lùi lại`;
            } else if (this.currentDistanceData.status === 'TOO_FAR') {
                strokeColor = "rgba(56, 189, 248, 0.85)"; // Sky Blue
                label = `⚠️ Quá xa camera (${this.currentDistanceData.distance_cm} cm) - Vui lòng tiến lại gần`;
            }
        }

        this.ctx.strokeStyle = strokeColor;
        this.ctx.setLineDash([8, 6]);

        this.ctx.beginPath();
        this.ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
        this.ctx.stroke();

        // Guide text banner
        this.ctx.setLineDash([]);
        this.ctx.fillStyle = "rgba(9, 13, 22, 0.85)";
        this.ctx.fillRect(centerX - 170, centerY + radiusY + 12, 340, 26);
        this.ctx.strokeStyle = strokeColor;
        this.ctx.strokeRect(centerX - 170, centerY + radiusY + 12, 340, 26);

        this.ctx.fillStyle = "#ffffff";
        this.ctx.font = "bold 11px 'Be Vietnam Pro', sans-serif";
        this.ctx.textAlign = "center";
        this.ctx.fillText(label, centerX, centerY + radiusY + 29);

        this.ctx.restore();
    }

    // 2. High-speed Live Computer Vision Frame Tracker
    async runLiveFaceTracker() {
        if (!this.isRunning || this.currentSource !== 'camera') return;

        if (this.video.readyState >= 2 && !this.isPostingFrame) {
            this.isPostingFrame = true;
            try {
                const offscreen = document.createElement('canvas');
                offscreen.width = 320;
                offscreen.height = 240;
                const offCtx = offscreen.getContext('2d');
                offCtx.drawImage(this.video, 0, 0, 320, 240);
                const b64 = offscreen.toDataURL('image/jpeg', 0.65);

                const res = await fetch('/api/cv/track-frame', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: b64 })
                });

                const data = await res.json();
                if (data.has_face) {
                    this.hasValidFace = true;
                    this.lastTrackTime = Date.now();

                    this.currentDistanceData = {
                        distance_cm: data.estimated_distance_cm,
                        status: data.distance_status,
                        advice: data.distance_advice
                    };

                    const scaleX = this.canvas.width / 320;
                    const scaleY = this.canvas.height / 240;

                    this.targetBox = {
                        center_x: data.glasses_position.center_x * scaleX,
                        center_y: data.glasses_position.center_y * scaleY,
                        width: data.glasses_position.width * scaleX,
                        height: data.glasses_position.height * scaleY,
                        angle: data.glasses_position.angle
                    };

                    this.currentLandmarks = (data.landmarks || []).map(pt => ({
                        x: pt.x * scaleX,
                        y: pt.y * scaleY
                    }));

                    if (this.options.onFaceAnalyzed) {
                        this.options.onFaceAnalyzed(data);
                    }
                } else {
                    if (Date.now() - this.lastTrackTime > 600) {
                        this.hasValidFace = false;
                        this.targetBox = null;
                        this.currentBox = null;
                        if (this.options.onFaceLost) {
                            this.options.onFaceLost();
                        }
                    }
                }
            } catch (err) {}
            this.isPostingFrame = false;
        }

        if (this.isRunning) {
            setTimeout(() => this.runLiveFaceTracker(), 120);
        }
    }

    stopCamera() {
        this.isRunning = false;
        this.currentSource = 'idle';
        this.hasValidFace = false;
        this.targetBox = null;
        this.currentBox = null;

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
        }
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.notifyStatus('Camera đã tắt', 'idle');
    }

    // Static Image Processing
    async processStaticImage(imgElement, serverVerifiedData = null) {
        this.stopCamera();
        this.staticImage = imgElement;
        this.currentSource = 'image';
        this.targetBox = null;
        this.currentBox = null;

        const w = imgElement.naturalWidth || imgElement.width || 640;
        const h = imgElement.naturalHeight || imgElement.height || 480;
        this.canvas.width = w;
        this.canvas.height = h;

        if (serverVerifiedData) {
            if (serverVerifiedData.has_face) {
                this.hasValidFace = true;
                this.targetBox = serverVerifiedData.glasses_position;
                this.currentLandmarks = serverVerifiedData.landmarks || [];
                if (this.options.onFaceAnalyzed) {
                    this.options.onFaceAnalyzed(serverVerifiedData);
                }
            } else {
                this.hasValidFace = false;
                if (this.options.onNoFaceDetected) {
                    this.options.onNoFaceDetected(serverVerifiedData.message || 'Không phát hiện khuôn mặt');
                }
            }
        } else {
            this.hasValidFace = false;
        }

        this.renderStaticFrame();
    }

    renderStaticFrame() {
        if (this.currentSource !== 'image' || !this.staticImage) return;

        const width = this.canvas.width;
        const height = this.canvas.height;

        this.ctx.save();
        this.ctx.clearRect(0, 0, width, height);
        this.ctx.drawImage(this.staticImage, 0, 0, width, height);

        // ONLY draw glasses if an actual verified face exists!
        if (this.hasValidFace && this.targetBox && this.isGlassesLoaded) {
            const box = this.targetBox;
            this.ctx.save();
            this.ctx.translate(box.center_x, box.center_y);
            this.ctx.rotate(box.angle || 0);
            this.ctx.drawImage(
                this.glassesImage,
                -box.width / 2,
                -box.height / 2,
                box.width,
                box.height
            );
            this.ctx.restore();
        }

        this.ctx.restore();
    }
}
