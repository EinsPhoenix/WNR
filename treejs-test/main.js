// main.js

// Globale Variablen
let camera, scene, renderer, raycaster;
let objectManager;
let renderManager;
let cameraController;
let octree;
let loadingIndicator;
let fileInput;
let dropZone;
let jsonData = null;
let SPACE_SIZE = 50000;
let disableAnimations = false;
let frustumCulling = true;
let octreeEnabled = false;
let fpsSamples = [];
let useAdaptivePerformance = true;
let frameCount = 0; 

window.eventBus = new EventTarget();

// Initializes the 3D visualization environment
function init() {
 
  loadingIndicator = document.getElementById('loading');
  fileInput = document.getElementById('fileInput');
  dropZone = document.getElementById('dropZone');

  document.getElementById('selectFileBtn').addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', handleFileSelect);

  setupDropZone();

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);

  addStarsToScene();

  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 20000);
  camera.position.set(0, 0, 1000);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({
    antialias: false,  
    powerPreference: "high-performance",
    logarithmicDepthBuffer: false, 
    precision: "mediump" 
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); 
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  raycaster = new THREE.Raycaster();

  objectManager = new ObjectManager(scene, camera);
  window.objectManager = objectManager; 

  renderManager = new RenderManager(renderer, camera, scene);
  renderManager.init();

  renderer.domElement.addEventListener('click', handleClick);
  
  cameraController = new CameraController(camera, renderer.domElement);

  window.addEventListener('resize', onWindowResize);
  window.addStarsToScene = addStarsToScene;

  window.eventBus.addEventListener('renderOptionChanged', (event) => {
    disableAnimations = event.detail.disableAnimations;
    if (objectManager) {
      objectManager.setDisableNiceMeshes(event.detail.disableNiceMeshes);
      if (event.detail.useLOD !== undefined) {
        objectManager.setUseLOD(event.detail.useLOD);
      }
    }
    SPACE_SIZE = event.detail.spaceSize;
    objectManager.updateGroundLightCircle(SPACE_SIZE);
  });

  setupLighting();
  
  window.addEventListener('keydown', handleKeyDown);
  
  animate();
}

// Configures the drop zone for file uploads
function setupDropZone() {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#4CAF50';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#ccc';
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#ccc';

    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });
}

// Sets up lighting elements in the 3D scene
function setupLighting() {
  const groundLight = objectManager.addGroundLightCircle(SPACE_SIZE);
  scene.add(groundLight);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  ambientLight.position.set(0, 0, 0);
  scene.add(ambientLight);

  const pointLight = new THREE.PointLight(0xffffff, 0.8);
  pointLight.position.set(0, 0, 0);
  scene.add(pointLight);
}

// Creates and adds stars to the background
function addStarsToScene(visible = true, enhancedQuality = false) {
  const existingStars = scene.getObjectByName("background-stars");
  if (existingStars) {
    scene.remove(existingStars);
  }
  
  if (!visible) return;
  
  const starsGeometry = new THREE.BufferGeometry();
  const starCount = enhancedQuality ? 20000 : 10000;
  
  const positions = new Float32Array(starCount * 3);
  const sizes = new Float32Array(starCount);
  const colors = new Float32Array(starCount * 3);
  
  const starColors = [
    new THREE.Color(0xFFFFFF),
    new THREE.Color(0xFFEECC),
    new THREE.Color(0xCCDDFF),
    new THREE.Color(0xFFDDAA),
    new THREE.Color(0xAAFFFF)
  ];
  
  for (let i = 0; i < starCount; i++) {
    const radius = SPACE_SIZE * 2 + Math.random() * SPACE_SIZE; 
    const theta = 2 * Math.PI * Math.random();
    const phi = Math.acos(2 * Math.random() - 1);
    
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = radius * Math.cos(phi);
    
    sizes[i] = enhancedQuality ? 
      0.3 + Math.pow(Math.random(), 2) * 3.0 :
      0.5 + Math.random() * 1.5;
    
    const color = starColors[Math.floor(Math.random() * starColors.length)];
    
    const r = color.r + (Math.random() * 0.1 - 0.05);
    const g = color.g + (Math.random() * 0.1 - 0.05);
    const b = color.b + (Math.random() * 0.1 - 0.05);
    
    colors[i * 3] = r;
    colors[i * 3 + 1] = g;
    colors[i * 3 + 2] = b;
  }
  
  starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  starsGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
  starsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  
  const starsMaterial = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      pixelRatio: { value: window.devicePixelRatio }
    },
    vertexShader: `
      attribute float size;
      attribute vec3 color;
      uniform float time;
      uniform float pixelRatio;
      varying vec3 vColor;
      
      void main() {
        vColor = color;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        
        float pulse = 0.9 + 0.2 * sin(time * 0.5 + position.x * 0.01 + position.y * 0.01);
        
        gl_PointSize = size * pulse * pixelRatio * (300.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      
      void main() {
        vec2 center = gl_PointCoord - 0.5;
        float dist = length(center);
        float alpha = 1.0 - smoothstep(0.4, 0.5, dist);
        
        gl_FragColor = vec4(vColor, alpha);
      }
    `,
    blending: THREE.AdditiveBlending,
    depthTest: false,
    transparent: true
  });
  
  const stars = new THREE.Points(starsGeometry, starsMaterial);
  stars.name = "background-stars";
  
  stars.userData.animate = function(time) {
    if (this.material && this.material.uniforms && this.material.uniforms.time) {
      this.material.uniforms.time.value = time * 0.1;
    }
  };
  
  scene.add(stars);
  
  return stars;
}

// Processes user clicks in the 3D environment
function handleClick(event) {
  const mouse = new THREE.Vector2();
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  
  if (objectManager) {
    objectManager.handleClick(mouse);
  }
}

// Clears any selected nodes
function clearSelection() {
  if (objectManager) {
    objectManager.clearSelection();
  }
}

// Processes file selection from input element
function handleFileSelect(event) {
  if (event.target.files.length) {
    handleFile(event.target.files[0]);
  }
}

// Processes an uploaded file
function handleFile(file) {
  if (file.type !== 'application/json') {
    alert('Bitte wähle eine JSON-Datei aus.');
    return;
  }
  
  dropZone.style.display = 'none';
  loadingIndicator.textContent = 'Lade JSON-Daten...';
  
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      jsonData = JSON.parse(e.target.result);
      processDataWithWorker(jsonData);
    } catch (error) {
      loadingIndicator.textContent = 'Fehler beim Parsen der JSON-Datei';
      console.error('JSON Parse Error:', error);
    }
  };
  reader.readAsText(file);
}

// Processes JSON data in a separate thread
function processDataWithWorker(jsonData, initialSpaceSize = SPACE_SIZE) {
    console.log(SPACE_SIZE);
    loadingIndicator.textContent = 'Verarbeite Daten in einem separaten Thread...';
    
    const workerBlob = new Blob([`
      self.onmessage = function(e) {
        const data = e.data.jsonData;
        const spaceSize = e.data.spaceSize;
        const processedData = processData(data, spaceSize);
        self.postMessage(processedData);
      };
      
      function processData(data, SPACE_SIZE) {
        const nodes = new Map();
        const relationships = [];
        const MIN_DISTANCE = 100;
        
        data.forEach(entry => {
          entry.forEach(item => {
            if (item.type === 'node' && !nodes.has(item.id)) {
              nodes.set(item.id, {
                id: item.id,
                labels: item.labels,
                properties: item.properties,
                position: getRandomPosition(SPACE_SIZE),
                connections: 0
              });
            } else if (item.type === 'relationship') {
              relationships.push({
                id: item.id,
                label: item.label,
                startId: item.start.id,
                endId: item.end.id
              });
              
              if (nodes.has(item.start.id)) {
                nodes.get(item.start.id).connections++;
              }
              if (nodes.has(item.end.id)) {
                nodes.get(item.end.id).connections++;
              }
            }
          });
        });
        
        function getRandomPosition(size) {
          return {
            x: (Math.random() - 0.5) * size,
            y: (Math.random() - 0.5) * size,
            z: (Math.random() - 0.5) * size
          };
        }
        
        const nodePositions = Array.from(nodes.values());
        resolveCollisions(nodePositions, SPACE_SIZE);
        
        function resolveCollisions(nodeList, SPACE_SIZE) {
          const iterations = 10;
          
          for (let iter = 0; iter < iterations; iter++) {
            for (let i = 0; i < nodeList.length; i++) {
              for (let j = i + 1; j < nodeList.length; j++) {
                const node1 = nodeList[i];
                const node2 = nodeList[j];
                
                const dx = node2.position.x - node1.position.x;
                const dy = node2.position.y - node1.position.y;
                const dz = node2.position.z - node1.position.z;
                
                const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
                
                const size1 = 5 + Math.min(45, node1.connections * 5);
                const size2 = 5 + Math.min(45, node2.connections * 5);
                
                const minDist = MIN_DISTANCE + size1/2 + size2/2;
                
                if (distance < minDist) {
                  const force = (minDist - distance) / distance * 0.5;
                  
                  node1.position.x -= dx * force;
                  node1.position.y -= dy * force;
                  node1.position.z -= dz * force;
                  
                  node2.position.x += dx * force;
                  node2.position.y += dy * force;
                  node2.position.z += dz * force;
                }
              }
            }
          }
          
          for (const node of nodeList) {
            const halfSize = SPACE_SIZE / 2;
            node.position.x = Math.max(-halfSize, Math.min(halfSize, node.position.x));
            node.position.y = Math.max(-halfSize, Math.min(halfSize, node.position.y));
            node.position.z = Math.max(-halfSize, Math.min(halfSize, node.position.z));
          }
        }
        
        return {
          nodes: Array.from(nodes.entries()),
          relationships: relationships,
          spaceSize: SPACE_SIZE 
        };
      }
    `], { type: 'application/javascript' });
    
    const workerUrl = URL.createObjectURL(workerBlob);
    const worker = new Worker(workerUrl);
    
    worker.onmessage = function(e) {
      const processedData = e.data;
      
      const nodes = new Map(processedData.nodes);
      const relationships = processedData.relationships;
     
      createVisualization(nodes, relationships);
      
      worker.terminate();
      URL.revokeObjectURL(workerUrl);
      
      loadingIndicator.textContent = `${nodes.size} Nodes und ${relationships.length} Beziehungen geladen`;
    };
    
    worker.onerror = function(error) {
      console.error('Worker error:', error);
      loadingIndicator.textContent = 'Fehler bei der Datenverarbeitung';
    };
    
    worker.postMessage({
      jsonData: jsonData,
      spaceSize: initialSpaceSize
    });
  }

// Calculates appropriate space size based on node count
function calculateSpaceSize(nodeCount) {
  const baseSize = 5;
  return Math.max(baseSize, Math.min(baseSize * 3, baseSize + (nodeCount * 200)));
}

// Creates the visualization from processed data
function createVisualization(nodes, relationships) {
  objectManager.createVisualization(nodes, relationships);
}

// Handles window resize events
function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  
  renderManager.onWindowResize();
}

// Checks if the mouse is hovering over objects
function checkHover() {
  const mouse = new THREE.Vector2();
  
  mouse.x = (window.innerWidth / 2 / window.innerWidth) * 2 - 1;
  mouse.y = -(window.innerHeight / 2 / window.innerHeight) * 2 + 1;
  
  if (objectManager) {
    objectManager.checkHover(mouse);
  }
}

// Handles the animation loop
function animate() {
  requestAnimationFrame(animate);
  
  renderer.state.reset();
  renderer.autoClear = true;
  
  if (octreeEnabled && octree) {
    const frustum = new THREE.Frustum();
    frustum.setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(
        camera.projectionMatrix,
        camera.matrixWorldInverse
      )
    );
    octree.getVisibleNodes(frustum, true);
  }
  
  const delta = 0.01;
  
  cameraController.update(delta);
  
  if (objectManager && objectManager.dynamicRendering) {
    objectManager.updateDynamicNodeVisibility();
  }
  
  if (!disableAnimations) {
    if (!cameraController.isControlActive()) {
      checkHover();
    }
    if (objectManager) {
      objectManager.updateLabels();
    }
  }
  
  if (useAdaptivePerformance && renderManager) {
    monitorPerformance();
  }
  
  renderManager.render();

  const stars = scene.getObjectByName("background-stars");
  if (stars && stars.userData && stars.userData.animate && typeof stars.userData.animate === 'function') {
    stars.userData.animate(performance.now() * 0.001);
  }
}

// Monitors and adapts performance settings
function monitorPerformance() {
  if (frameCount % 30 !== 0) return;
  
  const currentFPS = renderManager.currentFPS;
  
  fpsSamples.push(currentFPS);
  if (fpsSamples.length > 5) {
    fpsSamples.shift();
  }
  
  const avgFPS = fpsSamples.reduce((a, b) => a + b, 0) / fpsSamples.length;
  
  if (avgFPS < 10 & window.useAdaptivePerformance) {
    
    if (!disableAnimations) {
      console.log("Performance optimization: Disabling animations");
      disableAnimations = true;
      if (objectManager) {
        objectManager.setPerformanceMode(true);
      }
      renderManager.setRenderDistance(Math.min(renderManager.getRenderDistance(), 5000));
    }
  } else if (avgFPS > 20 && disableAnimations & window.useAdaptivePerformance) {
    
    console.log("Performance good: Re-enabling some features");
    disableAnimations = false;
    if (objectManager) {
      objectManager.setPerformanceMode(false);
    }
  }
  else{
    disableAnimations = false;
  }
}

// Processes keyboard input
function handleKeyDown(event) {
  const key = event.key.toLowerCase();
  
  if (key === 'f' || key === 'from' || key === 'to' || 
      key === 'arrowleft' || key === 'arrowright') {
      if (objectManager) {
          objectManager.handleKeyNavigation(key);
      }
  }
}

window.clearSelection = clearSelection;


init();