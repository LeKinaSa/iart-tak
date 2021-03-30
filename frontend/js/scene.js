const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);

const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 1000);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);

function updateRenderWindow() {
	renderer.setSize(window.innerWidth, window.innerHeight);
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

function genBoard(size = 5) {
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

//wf, ww, wc, bf, bw, bc
function genPieceStack(x, z, stack) {
	let pieces = new Map();
	pieces.set('bf', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.8), darkmarble));
	pieces.set('wf', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 0.8), lightmarble));

	pieces.set('bw', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.2), darkmarble));
	pieces.set('ww', new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.8, 0.2), lightmarble));
	
	pieces.set('bc', new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.8, 16), darkmarble));
	pieces.set('wc', new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.8, 16), lightmarble));	

	for (let i = 0; i < stack.length; i++) {
		let piece = stack[i];
		let type = stack[i][1];

		const base = pieces.get(piece).clone();
		base.position.x = x;
		base.position.y = (i + 1) * 0.2 + (type !== 'f' ? 0.3 : 0);
		base.position.z = z;
		scene.add( base );
	}
}

console.log("Hi")

genBoard();
genPieceStack(-2, -2, ['bf', 'bf', 'bf', 'wc']);
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