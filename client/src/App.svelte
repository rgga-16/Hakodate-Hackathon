<script>
	import {onMount, onDestroy} from "svelte";

	let videoStream;
	let videoElement;
	let canvasElement;
	let captureImage;
	/**
	 * detected_labels = [
		* 	{
		* 		name: "bottle",
		* 		type: "PET bottles, bottles, and cans"
		* 	},
			{
				name: "shoe",
				type: "Burnable"
			}
	 * ]
	 */
	let detected_labels=[];
	let detected_image;

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
		detected_labels=[];
		detected_image=null;
		captureImage = capture();
		const response = await fetch("/analyze_image", {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({image: captureImage})
		});
		const json = await response.json();
		detected_labels = json["detection_labels"];
		const detected_impath = json["detection_image"];
		detected_image = 'data:image/jpeg;base64,' + detected_impath;

		console.log(detected_labels);


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

	<div class="row centered">
		<video id="webcam" autoplay></video>
		<canvas id="canvas" width="512" height="512" style="display: none;"></canvas>

		{#if captureImage}
			<img src={captureImage} alt="Captured Image" />
		{/if}

		{#if detected_image}
			<img src={detected_image} alt="Detected Image" />
		{/if}

		{#if detected_labels.length > 0}
			Detected Objects:
			<ul>
				{#each detected_labels as detected_label }
					<li>{detected_label.name} - {detected_label.type}</li>
				{/each}
			</ul>
		{:else }
			No objects detected
		{/if}



	</div>
	
	
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