const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);

const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 1000);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);

function updateRenderWindow() {
	renderer.setSize(window.innerWidth, window.innerHeight);
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix();
}
window.addEventListener('resize', updateRenderWindow);

document.body.appendChild(renderer.domElement);

const textureDarkWood = new THREE.TextureLoader().load('images/darkwood.png');
const textureLightWood = new THREE.TextureLoader().load('images/lightwood.png');
const textureDarkMarble = new THREE.TextureLoader().load('images/blackmarble.jpg');
const textureLightMarble = new THREE.TextureLoader().load('images/whitemarble.png');

const darkwood = new THREE.MeshBasicMaterial({ map: textureDarkWood });
const lightwood = new THREE.MeshBasicMaterial({ map: textureLightWood });

const darkmarble = new THREE.MeshBasicMaterial({ map: textureDarkMarble });
const lightmarble = new THREE.MeshBasicMaterial({ map: textureLightMarble });


const geometry = new THREE.BoxGeometry(0.8, 0.2, 0.8);
const cube = new THREE.Mesh(geometry, darkwood);
// scene.add( cube );


camera.position.x = 5;
camera.position.y = 5;
camera.position.z = 0;
camera.lookAt(0, 0, 0);

function animate() {
	requestAnimationFrame(animate);

	// cube.rotation.x += 0.01;
	// cube.rotation.y += 0.01;
	// cube.position.x += 0.01;

	renderer.render(scene, camera);
};

animate();

function generateBoard(size = 5) {
	const darkBase = new THREE.Mesh(new THREE.BoxGeometry(1, 0.2, 1), darkwood);
	const lightBase = new THREE.Mesh(new THREE.BoxGeometry(1, 0.2, 1), lightwood);

	let currentBase = lightBase;

	for (let z = 0; z < size; z++) {
		if (size % 2 === 0) {
			currentBase = currentBase === lightBase ? darkBase : lightBase;
		}
		
		for (let x = 0; x < size; x++) {
			const base = currentBase.clone();
			base.position.x = x - size / 2 + 0.5;
			base.position.y = 0;
			base.position.z = z - size / 2 + 0.5;

			currentBase = currentBase === lightBase ? darkBase : lightBase;

			scene.add(base);
		}
	}
}

const pieceGroup = new THREE.Group();

function addPieces(board) {
	pieceGroup.clear();

	for (let row = 0; row < board.length; ++row) {
		for (let col = 0; col < board.length; ++col) {
			let stack = board[row][col];
		}
	}
}

let pieceMap = new Map();
pieceMap.set('bf', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.8), darkmarble));
pieceMap.set('wf', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.8), lightmarble));

pieceMap.set('bw', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.2), darkmarble));
pieceMap.set('ww', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.2), lightmarble));

pieceMap.set('bc', new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.8, 16), darkmarble));
pieceMap.set('wc', new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.8, 16), lightmarble));	

function addStack(x, z, stack) {
	for (let i = 0; i < stack.length; i++) {
		let piece = stack[i];
		let type = stack[i][1];

		const pieceGeometry = pieceMap.get(piece).clone();
		pieceGeometry.position.x = x;
		pieceGeometry.position.y = (i + 1) * 0.2 + (type !== 'f' ? 0.3 : 0);
		pieceGeometry.position.z = z;
		pieceGroup.add(pieceGeometry);
	}
}

generateBoard();
// setTimeout(() => {for (let z = -2; z <= 2; z++) {
// 	for (let y = -2; y <= 2; y++) {
// 		for (let x = -2; x <= 2; x++) {
// 			const cube2 = cube.clone();
// 			cube2.position.x = x;
// 			cube2.position.y = y/4;
// 			cube2.position.z = z;
// 			scene.add( cube2 );
// 			console.log(x)
// 		}
// 	}
// 	}

// }, 2000);


// A sum example
//
var xhr = new XMLHttpRequest();
var url = "http://localhost:8001/sum";
xhr.open("POST", url, true);
xhr.setRequestHeader("Content-Type", "application/json");
xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
        var json = JSON.parse(xhr.responseText);
        console.log(json);
    }
};
var data = JSON.stringify({"numbers" : [1, 2, 3, 4]});
xhr.send(data);

/*
 *  Code related to User Interface controls
 */

const gameTypeControls = document.getElementById('gameTypeControls');
gameTypeControls.classList.remove("d-none");

function onGameTypeSubmitted(event) {
	event.preventDefault();

	let request = new XMLHttpRequest();
	let url = 'http://localhost:8001/start_game';
	request.open('POST', url, true);
	request.setRequestHeader('Content-Type', 'application/json');
	request.addEventListener('load', (event) => {
		event.preventDefault();
		let response = JSON.parse(request.responseText);
		// TODO: update board
		console.log(response);
	});

	let size = Number.parseInt(document.getElementById('boardSize').value);
	let whiteType = document.getElementById('whiteType').value;
	let blackType = document.getElementById('blackType').value;

	let data = JSON.stringify({size: size, white_type: whiteType, black_type: blackType});
	request.send(data);
}

gameTypeControls.querySelector('form').addEventListener('submit', onGameTypeSubmitted);

const moveTypes = {
	PlaceFlat: {params: ['pos']},
	PlaceWall: {params: ['pos']},
	PlaceCap: {params: ['pos']},
	MovePiece: {params: ['pos', 'direction']},
	SplitStack: {params: ['pos', 'direction', 'split']}
};

function showParams(params) {
	let paramsDiv = document.getElementById('moveParams');
	paramsDiv.innerHTML = "";

	for (let param of params) {
		if (param === 'pos') {
			let posDiv = document.createElement('div');
			posDiv.classList.add('mb-2');
			posDiv.innerHTML = '<label class="form-label" for="row">Row</label><input class="form-control"' +
					'type="number" id="row" min="1" max="5" value="1">';
			paramsDiv.appendChild(posDiv);
		}
		else if (param === 'direction') {

		}
	}
}

function showMoveTypes(possibleMoves) {
	let possibleTypes = new Set();

	for (let move of possibleMoves) {
		if (moveTypes[move.type] != null) {
			possibleTypes.add(move.type);
		}
	}

	let moveTypeSelect = document.getElementById('moveType');
	moveTypeSelect.innerHTML = "";

	for (let type of possibleTypes) {
		let option = document.createElement('option');
		option.innerHTML = type;
		option.value = type;
		moveTypeSelect.appendChild(option);
	}

	showParams(moveTypes[moveTypeSelect.value].params);

	moveTypeSelect.addEventListener('change', (event) => {
		showParams(moveTypes[event.target.value].params);
	});
}
