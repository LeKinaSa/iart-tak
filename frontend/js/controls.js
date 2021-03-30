
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

showMoveTypes([{'type': 'MovePiece'}, {'type': 'PlaceFlat'}, {'type': 'MovePiece'}])