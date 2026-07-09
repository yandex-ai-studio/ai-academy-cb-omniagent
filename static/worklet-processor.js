                class WebsocketAudioProcessor extends AudioWorkletProcessor {

                    constructor() {
                        super();
                        this.buffer = [];
                        this.lastSendTime = 0;
                    }

                    process(inputs, outputs, parameters) {
                        
                        // Mono channel input
                        const input = inputs[0];
                        
                        if (input[0]?.length) {

                // Convert Float32Array to Int16Array for efficient sending
                            const int16Data = new Int16Array(input[0].length);
                            for (let i = 0; i < input[0].length; i++) {
                                let sample = Math.max(-1, Math.min(1, input[0][i]))
                                // int16Data[i] = sample < 0 ? sample* 0*8000 : sample * 0x7FFF;
                                int16Data[i] = Math.max(-1, Math.min(1, input[0][i])) * 0x7FFF; // Scale to 16-bit signed integer
                            }
                            this.buffer.push(...int16Data);
                        }

                        // Send every x ms
                        if (currentTime - this.lastSendTime >= 0.20) {
                            // console.log('Flush buffer: ', this.buffer);
                            
                            if (this.buffer.length) {
                                // console.log('Sending buffer length: ', this.buffer.length);
                                // const blob = new Blob([this.buffer], { type: 'application/octet-stream' });
                                

                                this.port.postMessage(new Uint16Array(this.buffer));
                                this.buffer = [];
                            }
                            this.lastSendTime = currentTime;
                        }
                        
                        // Всегда возвращаем true, чтобы процессор продолжал работать
                        return true;
                    }
                }
                registerProcessor('websocket-audio-processor', WebsocketAudioProcessor);