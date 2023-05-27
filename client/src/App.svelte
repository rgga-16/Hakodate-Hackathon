<script>
	import {onMount, onDestroy} from "svelte";

	let videoStream;
	let videoElement;
	let canvasElement;
	let captureImage;

	async function startWebcam() {
		try {
			videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
			videoElement.srcObject = videoStream;
		} catch (error) {
			console.error("Error accessing webcam:", error);
		}
	}

	function stopWebcam() {
		if (videoStream) {
			videoStream.getTracks().forEach((track) => track.stop());
			videoElement.srcObject = null;
			videoStream = null;
		}
	}

	function capture() {
		const context = canvasElement.getContext("2d");
		context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
		return canvasElement.toDataURL("image/png");
	}

	async function analyzeImage() {
		captureImage = capture();
		const response = await fetch("/analyze_image", {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({image: captureImage})
		});

	}



	onMount(() => {
		captureImage = null;
		videoElement = document.getElementById("webcam");
		canvasElement = document.getElementById("canvas");

		startWebcam();
	});

	onDestroy(() => {
		stopWebcam();
	});

</script>

<div class="column centered">
	<h3> TrashScan</h3>

	<video id="webcam" autoplay></video>
	<canvas id="canvas" width="512" height="512" style="display: none;"></canvas>

	{#if captureImage}
    	<img src={captureImage} alt="Captured Image" />
  	{/if}

	
	<!-- <button on:click={startWebcam}>Start Webcam</button> -->
	<!-- <button on:click={stopWebcam}>Stop Webcam</button> -->
	<button on:click={analyzeImage}>Analyze Image</button>
</div>



<style>
	#webcam {
		width: 50%;
		height: 50%;
	}
</style>