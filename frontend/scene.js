const scene = new THREE.Scene();
			
const camera = new THREE.PerspectiveCamera( 70, window.innerWidth / window.innerHeight, 1, 1000 );
camera.position.z = 400;

const renderer = new THREE.WebGLRenderer();
renderer.setSize( window.innerWidth, window.innerHeight );
document.body.appendChild( renderer.domElement );

const texture = new THREE.TextureLoader().load('crate.gif');
const material = new THREE.MeshBasicMaterial( { map: texture } );

const geometry = new THREE.BoxGeometry();
const cube = new THREE.Mesh( geometry, material );
const cube2 = cube.clone();
cube2.position.x = 2;
scene.add( cube );
scene.add( cube2 );

camera.position.z = 5;

const animate = function () {
	requestAnimationFrame( animate );

	// cube.rotation.x += 0.01;
	// cube.rotation.y += 0.01;
    // cube.position.x += 0.01;

	renderer.render( scene, camera );
};

animate();