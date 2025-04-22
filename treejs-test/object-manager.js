// object-manager.js
class ObjectManager {
    constructor(scene, camera) {
      this.scene = scene;
      this.camera = camera;
      this.nodes = new Map();
      this.relationships = [];
      this.nodeObjects = new Map();
      this.nodeLabels = new Map();
      this.lineObjects = [];
      this.lineLabels = [];
      this.hoveredObject = null;
      this.selectedObject = null;
      this.labelColorMap = new Map();
      this.nextColorIndex = 0;
      this.infoPanel = document.getElementById('info');
      this.loadingIndicator = document.getElementById('loading');
      this.MIN_DISTANCE = 100;
      this.disableNiceMeshes = false;
      this.groundLightCircle = null;  
      this.useLOD = true; 
      this.frustumCulled = true;  
      this.instancedNodes = null; 
      this.visibleNodes = new Set(); 
      this.maxVisibleDistance = 15000; 
      this.isPerformanceModeEnabled = false;
  
      this.neonColors = [
        0xff00ff, // Magenta
        0x00ffff, // Cyan
        0xff0066, // Pink
        0x00ff00, // Grün
        0xff3300, // Orange
        0x9900ff, // Lila
        0x00ccff, // Hellblau
        0xffff00, // Gelb
        0xff0000, // Rot
        0x0000ff  // Blau
      ];
  
      this.raycaster = new THREE.Raycaster();
    }
  
  
    setDisableNiceMeshes(value) {
      this.disableNiceMeshes = value;
    }
  
    setUseLOD(value) {
      this.useLOD = value;

      if (this.nodeObjects.size > 0) {
        this.updateNodeLODs();
      }
    }
  
    updateNodeLODs() {
      for (const [id, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(id);
        if (nodeData) {
          this.updateNodeLOD(nodeObject, nodeData, this.camera.position);
        }
      }
    }
  
    updateNodeLOD(nodeObject, nodeData, cameraPosition, forceQualityCheck = false) {
      if (!this.useLOD || !nodeObject) return;
      
      const distance = cameraPosition.distanceTo(nodeObject.position);
  
      const connections = nodeData.connections || 0;
      const baseSize = 20 + Math.min(70, connections * 5);
      
      // Add hysteresis to LOD transitions to prevent flickering
      const farThreshold = 10000;
      const mediumThreshold = 3000;
      
    
      const previousLOD = nodeObject.userData.currentLOD;
      const isNewNode = previousLOD === undefined || previousLOD === 'none';
      
  
      const isQualityMode = window.currentQualityMode === 'quality';
      

      let lodChanged = false;
      
      
      if (nodeObject.userData.currentLOD === 'far' && distance > farThreshold * 0.9) {
      
      } else if (nodeObject.userData.currentLOD === 'medium' && 
                 distance > mediumThreshold * 0.9 && 
                 distance < farThreshold * 1.1) {
     
      } else {
        // Decide LOD based on distance
        if (distance > farThreshold) {
          if (nodeObject.userData.currentLOD !== 'far') {
            this.applyFarLOD(nodeObject, nodeData, baseSize, isQualityMode);
            nodeObject.userData.currentLOD = 'far';
            lodChanged = true;
          }
        } else if (distance > mediumThreshold) {
          if (nodeObject.userData.currentLOD !== 'medium') {
            this.applyMediumLOD(nodeObject, nodeData, baseSize, isQualityMode);
            nodeObject.userData.currentLOD = 'medium';
            lodChanged = true;
          }
        } else {
          if (nodeObject.userData.currentLOD !== 'close') {
            this.applyCloseLOD(nodeObject, nodeData, baseSize, isQualityMode);
            nodeObject.userData.currentLOD = 'close';
            lodChanged = true;
          }
        }
      }
      
     
      if ((lodChanged || forceQualityCheck || isNewNode) && isQualityMode && !nodeObject.userData.qualityApplied) {
        this.applyNodeQualityEffects(nodeObject, nodeData);
      }
      
   
      if (distance > this.maxVisibleDistance * 1.1) {
        if (nodeObject.visible) {
          nodeObject.visible = false;
          if (this.nodeLabels.has(nodeData.id)) {
            this.nodeLabels.get(nodeData.id).visible = false;
          }
        }
      } else if (distance < this.maxVisibleDistance * 0.9 && !nodeObject.visible) {
        nodeObject.visible = true;
        if (this.nodeLabels.has(nodeData.id)) {
          this.nodeLabels.get(nodeData.id).visible = true;
        }
      }
    }
  
    applyFarLOD(nodeObject, nodeData, baseSize, isQualityMode) {
      
    
      this.cleanupNodeMeshResources(nodeObject);
      
      const primaryLabel = nodeData.labels[0] || `Node ${nodeData.id}`;
      const color = this.getColorForLabel(primaryLabel);
      
    
      if (window.currentQualityMode === 'performance') {
       
        nodeObject.geometry = new THREE.TetrahedronGeometry(baseSize * 0.8, 0);
        
      
        nodeObject.material = new THREE.MeshBasicMaterial({
          color: color,
          flatShading: true
        });
        
        return;
      }
      
      
      nodeObject.geometry = new THREE.OctahedronGeometry(baseSize * 0.8, 0);
      
     
      if (isQualityMode) {
        
        nodeObject.material = new THREE.MeshPhysicalMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.4,
          metalness: 0.7,
          roughness: 0.4,
          envMap: window.renderManager ? window.renderManager.envMap : null,
          envMapIntensity: 0.8,
          clearcoat: 0.3,
          clearcoatRoughness: 0.2,
          reflectivity: 0.5
        });
        
        
        const glowGeometry = new THREE.SphereGeometry(baseSize * 1.2, 8, 6);
        const glowMaterial = new THREE.MeshBasicMaterial({
          color: color,
          transparent: true,
          opacity: 0.2,
          side: THREE.BackSide
        });
        
        const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
        nodeObject.add(glowMesh);
        
     
        nodeObject.userData.atmosphereLayers = [glowMesh];
      } else {
       
        nodeObject.material = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.3,
          metalness: 0.6,
          roughness: 0.8
        });
      }
    }
  
    applyMediumLOD(nodeObject, nodeData, baseSize, isQualityMode) {
      
      this.cleanupNodeMeshResources(nodeObject);
      
      const primaryLabel = nodeData.labels[0] || `Node ${nodeData.id}`;
      const color = this.getColorForLabel(primaryLabel);
      
     
      nodeObject.geometry = new THREE.SphereGeometry(baseSize * 0.8, 16, 12);
      
      
      const envMap = window.renderManager ? window.renderManager.envMap : null;

      if (window.currentQualityMode === 'performance') {
       
        nodeObject.geometry = new THREE.TetrahedronGeometry(baseSize * 0.8, 8, 6);
        
     
        nodeObject.material = new THREE.MeshBasicMaterial({
          color: color,
          flatShading: true
        });
        
        return;
      }
      
      if (isQualityMode) {
      
        nodeObject.material = new THREE.MeshPhysicalMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.4,
          metalness: 0.7,
          roughness: 0.3,
          envMap: envMap,
          envMapIntensity: 0.8,
          clearcoat: 0.6,
          clearcoatRoughness: 0.2,
          reflectivity: 0.7
        });

        const nodeRadius = nodeObject.geometry.parameters.radius;
        this.addAtmosphericEffects(nodeObject, color, nodeRadius);

        this.addCloudLayer(nodeObject, color, envMap);
      } else {
    
        const innerGeometry = new THREE.SphereGeometry(baseSize * 0.7, 16, 12);
        const innerMaterial = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.4,
          metalness: 0.6,
          roughness: 0.5
        });
        
        const innerMesh = new THREE.Mesh(innerGeometry, innerMaterial);
        
     
        nodeObject.geometry = new THREE.SphereGeometry(baseSize * 0.9, 16, 12);
        nodeObject.material = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.2,
          transparent: true,
          opacity: 0.5,
          metalness: 0.4,
          roughness: 0.8
        });
        
        nodeObject.add(innerMesh);
      }
    }
  
    applyCloseLOD(nodeObject, nodeData, baseSize, isQualityMode) {
      
      this.cleanupNodeMeshResources(nodeObject);
      
      const innerSize = baseSize * 0.8;
      const primaryLabel = nodeData.labels[0] || `Node ${nodeData.id}`;
      const color = this.getColorForLabel(primaryLabel);
  
      const envMap = window.renderManager ? window.renderManager.envMap : null;
      
      
      
      if (window.currentQualityMode === 'performance') {
       
        nodeObject.geometry = new THREE.TetrahedronGeometry(baseSize * 0.8, 16, 12);
        
     
        nodeObject.material = new THREE.MeshBasicMaterial({
          color: color,
          flatShading: true
        });
        
        return;
      }

      
      
      if (isQualityMode) {
    
        const innerGeometry = new THREE.SphereGeometry(innerSize, 32, 32);
        const innerMaterial = new THREE.MeshPhysicalMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.5,
          metalness: 0.8,
          roughness: 0.2,
          envMap: envMap,
          envMapIntensity: 1.0,
          clearcoat: 0.8,
          clearcoatRoughness: 0.1,
          reflectivity: 0.9,
          ior: 1.5
        });
    
        const innerMesh = new THREE.Mesh(innerGeometry, innerMaterial);
        innerMesh.position.set(0, 0, 0);
        
        // Outer shell with transparency
        const outerGeometry = new THREE.SphereGeometry(baseSize, 32, 32);
        const outerMaterial = new THREE.MeshPhysicalMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.3,
          transparent: true,
          opacity: 0.7,
          metalness: 0.7,
          roughness: 0.3,
          envMap: envMap,
          envMapIntensity: 0.9,
          clearcoat: 0.6,
          clearcoatRoughness: 0.2,
          reflectivity: 0.8,
          transmission: 0.2,
          ior: 1.3
        });
    
        nodeObject.geometry = outerGeometry;
        nodeObject.material = outerMaterial;
        nodeObject.add(innerMesh);
        
  
        const nodeRadius = nodeObject.geometry.parameters.radius;
        this.addAtmosphericEffects(nodeObject, color, nodeRadius);
        this.addCloudLayer(nodeObject, color, envMap);
      } else {
      
        const innerGeometry = new THREE.SphereGeometry(baseSize * 0.7, 20, 20);
        const innerMaterial = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.4,
          metalness: 0.6,
          roughness: 0.5
        });
        
        const innerMesh = new THREE.Mesh(innerGeometry, innerMaterial);
        
       
        nodeObject.geometry = new THREE.SphereGeometry(baseSize * 0.95, 20, 20);
        nodeObject.material = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.2,
          transparent: true,
          opacity: 0.6,
          metalness: 0.5,
          roughness: 0.7
        });
        
        nodeObject.add(innerMesh);
        
        // Add a simplified glow effect
        const glowGeometry = new THREE.SphereGeometry(baseSize * 1.1, 16, 12);
        const glowMaterial = new THREE.MeshBasicMaterial({
          color: color,
          transparent: true,
          opacity: 0.1,
          side: THREE.BackSide
        });
        
        const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
        nodeObject.add(glowMesh);
        nodeObject.userData.atmosphereLayers = [glowMesh];
      }
    }

    addAtmosphericEffects(nodeObject, color, nodeRadius) {
    
      if (nodeObject.userData.atmosphereLayers) {
        nodeObject.userData.atmosphereLayers.forEach(layer => {
          if (layer.geometry) layer.geometry.dispose();
          if (layer.material) layer.material.dispose();
          nodeObject.remove(layer);
        });
      }
      
      nodeObject.userData.atmosphereLayers = [];
   
      const innerGlowGeometry = new THREE.SphereGeometry(nodeRadius * 1.1, 32, 32);
      const innerGlowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.2,
        side: THREE.BackSide
      });
      
      const innerGlow = new THREE.Mesh(innerGlowGeometry, innerGlowMaterial);
      nodeObject.add(innerGlow);
      nodeObject.userData.atmosphereLayers.push(innerGlow);
      
  
      const outerGlowGeometry = new THREE.SphereGeometry(nodeRadius * 1.4, 24, 24);
      const outerGlowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.1,
        side: THREE.BackSide
      });
      
      const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
      nodeObject.add(outerGlow);
      nodeObject.userData.atmosphereLayers.push(outerGlow);
      
   
      if (Math.random() > 0.6) {
        const ringGeometry = new THREE.RingGeometry(
          nodeRadius * 1.5, 
          nodeRadius * 2.2, 
          64
        );
        
      
        ringGeometry.rotateX(Math.PI / 2);
        
        const ringColor = new THREE.Color(color);
        ringColor.offsetHSL(0, -0.2, 0.2); 
        
        const ringMaterial = new THREE.MeshPhysicalMaterial({
          color: ringColor,
          transparent: true,
          opacity: 0.6,
          side: THREE.DoubleSide,
          envMap: window.renderManager ? window.renderManager.envMap : null,
          envMapIntensity: 0.5,
          metalness: 0.3,
          roughness: 0.7
        });
        
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      
        nodeObject.add(ring);
        nodeObject.userData.atmosphereLayers.push(ring);
      }
      
     
      const particleCount = 200;
      const particleGeometry = new THREE.BufferGeometry();
      const particlePositions = new Float32Array(particleCount * 3);
      const particleSizes = new Float32Array(particleCount);
      
      for (let i = 0; i < particleCount; i++) {
      
        const radius = nodeRadius * (1.05 + Math.random() * 0.3);
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        particlePositions[i * 3 + 2] = radius * Math.cos(phi);
        
        particleSizes[i] = 0.5 + Math.random() * 2.0; 
      }
      
      particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
      particleGeometry.setAttribute('size', new THREE.BufferAttribute(particleSizes, 1));
      
      const particleMaterial = new THREE.ShaderMaterial({
        uniforms: {
          color: { value: new THREE.Color(color).multiplyScalar(1.5) },
          time: { value: 0 }
        },
        vertexShader: `
          attribute float size;
          uniform float time;
          varying float vAlpha;
          
          void main() {
            vAlpha = 0.3 + 0.7 * sin(time * 2.0 + position.x * 10.0);
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            gl_PointSize = size * (300.0 / -mvPosition.z);
            gl_Position = projectionMatrix * mvPosition;
          }
        `,
        fragmentShader: `
          uniform vec3 color;
          varying float vAlpha;
          
          void main() {
            vec2 xy = gl_PointCoord.xy - vec2(0.5);
            float ll = length(xy);
            float alpha = step(ll, 0.5) * vAlpha;
            
            gl_FragColor = vec4(color, alpha);
          }
        `,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        transparent: true
      });
      
      const glitterParticles = new THREE.Points(particleGeometry, particleMaterial);
      glitterParticles.userData.animate = function(time) {
        this.material.uniforms.time.value = time;
      };
      nodeObject.add(glitterParticles);
      nodeObject.userData.atmosphereLayers.push(glitterParticles);
    }
    
    addCloudLayer(nodeObject, color, envMap) {
    
      if (nodeObject.userData.cloudLayers) {
        nodeObject.userData.cloudLayers.forEach(layer => {
          if (layer.geometry) layer.geometry.dispose();
          if (layer.material) layer.material.dispose();
          nodeObject.remove(layer);
        });
      }
      
      nodeObject.userData.cloudLayers = [];
      
      const nodeRadius = nodeObject.geometry.parameters.radius;
      
  
      const cloudLayerCount = 2 + Math.floor(Math.random() * 2); 
      
      for (let i = 0; i < cloudLayerCount; i++) {
        const layerHeight = 1.02 + (i * 0.03); 
        const cloudGeometry = new THREE.SphereGeometry(
          nodeRadius * layerHeight,
          32, 32
        );
        
      
        const cloudColor = new THREE.Color(color).lerp(new THREE.Color(0xffffff), 0.4 + (i * 0.2));
        
        const cloudMaterial = new THREE.MeshPhysicalMaterial({
          color: cloudColor,
          transparent: true,
          opacity: 0.4 - (i * 0.1),
          envMap: envMap,
          envMapIntensity: 0.5,
          roughness: 0.8,
          metalness: 0.2,
          clearcoat: 0.4,
          clearcoatRoughness: 0.5,
          transmission: 0.2,
          side: THREE.FrontSide,
          depthWrite: i === 0
        });
        

        const displacementMap = this.generateCloudTexture();
        cloudMaterial.displacementMap = displacementMap;
        cloudMaterial.displacementScale = (i + 1) * 2;
        cloudMaterial.displacementBias = -1 * (i + 1);
        
        const cloudMesh = new THREE.Mesh(cloudGeometry, cloudMaterial);
        
       
        cloudMesh.rotation.set(
          Math.random() * Math.PI * 2,
          Math.random() * Math.PI * 2,
          Math.random() * Math.PI * 2
        );
        
      
        cloudMesh.userData.initialRotation = cloudMesh.rotation.clone();
        cloudMesh.userData.rotationSpeed = 0.05 - (i * 0.02); 
        cloudMesh.userData.rotationAxis = new THREE.Vector3(
          Math.random() - 0.5,
          Math.random() - 0.5,
          Math.random() - 0.5
        ).normalize();
        
       
        cloudMesh.userData.animate = function(time) {
          const axis = this.userData.rotationAxis;
          const speed = this.userData.rotationSpeed;
          
          this.rotation.x = this.userData.initialRotation.x + time * speed * axis.x;
          this.rotation.y = this.userData.initialRotation.y + time * speed * axis.y;
          this.rotation.z = this.userData.initialRotation.z + time * speed * axis.z;
        };
        
        nodeObject.add(cloudMesh);
        
        if (!nodeObject.userData.cloudLayers) {
          nodeObject.userData.cloudLayers = [];
        }
        nodeObject.userData.cloudLayers.push(cloudMesh);
      }
    }
    
    generateCloudTexture() {
      
      const cacheKey = 'cloudTexture';
      
      if (window.renderManager && window.renderManager.textureCache && 
          window.renderManager.textureCache.has(cacheKey)) {
        return window.renderManager.textureCache.get(cacheKey);
      }
      
     
      const size = 512;
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      
      
      ctx.fillStyle = 'black';
      ctx.fillRect(0, 0, size, size);
      
     
      for (let i = 0; i < 40; i++) {
        const x = Math.random() * size;
        const y = Math.random() * size;
        const radius = 50 + Math.random() * 100;
        
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.4)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);
      }
      
    
      const texture = new THREE.CanvasTexture(canvas);
      texture.wrapS = THREE.RepeatWrapping;
      texture.wrapT = THREE.RepeatWrapping;
      
    
      if (window.renderManager && window.renderManager.textureCache) {
        window.renderManager.textureCache.set(cacheKey, texture);
      }
      
      return texture;
    }
    
    updateQualityAnimations(time) {
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        
        if (nodeObject.userData.atmosphereLayers) {
          nodeObject.userData.atmosphereLayers.forEach(layer => {
            if (layer.userData && layer.userData.animate) {
              layer.userData.animate(time);
            }
          });
        }
        
        // Animate cloud layers
        if (nodeObject.userData.cloudLayers) {
          nodeObject.userData.cloudLayers.forEach(layer => {
            if (layer.userData && layer.userData.animate) {
              layer.userData.animate(time);
            }
          });
        }
      }
    }
  
    createTextLabel(text, color = 0xffffff) {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.width = 256;
      canvas.height = 64;
      
     
      const r = (color >> 16) & 0xff;
      const g = (color >> 8) & 0xff;
      const b = color & 0xff;
      const colorString = `rgb(${r}, ${g}, ${b})`;
      
      // Clear canvas with transparency
      context.clearRect(0, 0, canvas.width, canvas.height);
      
     
      const padding = 8;
      const borderRadius = 12;
      const borderWidth = 2;
      
      let displayText = text;
      if (text.length > 20) {
        displayText = text.slice(0, 18) + '...';
      }
      
     
      context.font = 'Bold 20px Arial';
      const textMetrics = context.measureText(displayText);
      const textWidth = textMetrics.width;
      

      const bgWidth = textWidth + (padding * 2);
      const bgHeight = 28;
      
 
      const bgX = (canvas.width - bgWidth) / 2;
      const bgY = (canvas.height - bgHeight) / 2;
      
     
      context.fillStyle = colorString;
      this.roundRect(context, bgX, bgY, bgWidth, bgHeight, borderRadius);
      
    
      context.fillStyle = 'white';
      this.roundRect(
        context, 
        bgX + borderWidth, 
        bgY + borderWidth, 
        bgWidth - (borderWidth * 2), 
        bgHeight - (borderWidth * 2), 
        borderRadius - borderWidth
      );
      

      context.font = 'Bold 20px Arial';
      context.fillStyle = `rgb(40, 40, 40)`;  
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(displayText, canvas.width / 2, canvas.height / 2);
      
    
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
      
      const spriteMaterial = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        sizeAttenuation: true
      });
      
      const sprite = new THREE.Sprite(spriteMaterial);
      sprite.scale.set(200, 50, 1);
      
      return sprite;
    }
    
    
    roundRect(ctx, x, y, width, height, radius) {
      if (width < 2 * radius) radius = width / 2;
      if (height < 2 * radius) radius = height / 2;
      
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.arcTo(x + width, y, x + width, y + height, radius);
      ctx.arcTo(x + width, y + height, x, y + height, radius);
      ctx.arcTo(x, y + height, x, y, radius);
      ctx.arcTo(x, y, x + width, y, radius);
      ctx.closePath();
      ctx.fill();
    }
  
    getColorForLabel(label) {
      if (this.labelColorMap.has(label)) {
        return this.labelColorMap.get(label);
      }
      
      let color;
      
      if (this.nextColorIndex < this.neonColors.length) {
        color = this.neonColors[this.nextColorIndex];
        this.nextColorIndex++;
      } else {
        const baseColor = this.neonColors[this.nextColorIndex % this.neonColors.length];
        
        const variation = 0.2;
        const r = ((baseColor >> 16) & 0xff) / 255;
        const g = ((baseColor >> 8) & 0xff) / 255;
        const b = (baseColor & 0xff) / 255;
        
        const rNew = Math.max(0, Math.min(1, r + (Math.random() * variation * 2 - variation)));
        const gNew = Math.max(0, Math.min(1, g + (Math.random() * variation * 2 - variation)));
        const bNew = Math.max(0, Math.min(1, b + (Math.random() * variation * 2 - variation)));
        
        color = (Math.floor(rNew * 255) << 16) | 
                (Math.floor(gNew * 255) << 8) | 
                Math.floor(bNew * 255);
        
        this.nextColorIndex++;
      }
      
      this.labelColorMap.set(label, color);
      
      return color;
    }
  
    createNode(id, nodeData) {
      const size = 20 + Math.min(70, nodeData.connections * 5);
      
   
      const geometry = new THREE.SphereGeometry(size * 0.8, 8, 6);
      const primaryLabel = nodeData.labels[0] || `Node ${id}`;
      const color = this.getColorForLabel(primaryLabel);
      
      
      const isQualityMode = window.renderManager && window.currentQualityMode === 'quality';
      
     
      const material = isQualityMode ? 
        new THREE.MeshPhysicalMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.3,
          metalness: 0.7,
          roughness: 0.4,
          envMap: window.renderManager ? window.renderManager.envMap : null,
          envMapIntensity: 0.8,
          clearcoat: 0.6,
          clearcoatRoughness: 0.2,
          reflectivity: 0.8
        }) :
        new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.3
        });
      
      const nodeMesh = new THREE.Mesh(geometry, material);
      nodeMesh.position.set(
        nodeData.position.x,
        nodeData.position.y, 
        nodeData.position.z
      );
      
      nodeMesh.userData = {
        id: id,
        labels: nodeData.labels,
        properties: nodeData.properties,
        type: 'node',
        currentLOD: 'none',
        qualityApplied: isQualityMode 
      };
      
      nodeMesh.frustumCulled = this.frustumCulled;
      
      this.scene.add(nodeMesh);
      this.nodeObjects.set(id, nodeMesh);
      
      this.updateNodeLOD(nodeMesh, nodeData, this.camera.position, true); 
      
      
      if (isQualityMode) {
        this.applyNodeQualityEffects(nodeMesh, nodeData);
      }
      
      const labelText = primaryLabel;
      const labelSprite = this.createTextLabel(labelText, color);
      labelSprite.position.set(
        nodeData.position.x,
        nodeData.position.y + size + 30,
        nodeData.position.z
      );
      
      labelSprite.frustumCulled = this.frustumCulled;
      this.scene.add(labelSprite);
      this.nodeLabels.set(id, labelSprite);
    }
  
    createRelationship(relationship) {
      const startNode = this.nodeObjects.get(relationship.startId);
      const endNode = this.nodeObjects.get(relationship.endId);
      
      if (!startNode || !endNode) {
        console.warn('Beziehung mit fehlendem Node:', relationship);
        return;
      }
      
      const points = [
        startNode.position.clone(),
        endNode.position.clone()
      ];
      
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      
      const material = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.2
      });
      
      const line = new THREE.Line(geometry, material);
      
      line.userData = {
        id: relationship.id,
        label: relationship.label,
        startId: relationship.startId,
        endId: relationship.endId,
        type: 'relationship'
      };
      

      line.frustumCulled = false;
      
      this.scene.add(line);
      this.lineObjects.push(line);
      
      const labelText = relationship.label || `Rel ${relationship.id}`;
      const labelSprite = this.createTextLabel(labelText, 0xffff00); 
      
      const midPoint = new THREE.Vector3().addVectors(
        startNode.position,
        endNode.position
      ).multiplyScalar(0.5);
      
      midPoint.y += 20;
      
      labelSprite.position.copy(midPoint);
      labelSprite.frustumCulled = false; 
      
 
      labelSprite.visible = line.visible;
      
      this.scene.add(labelSprite);
      this.lineLabels.push({
        sprite: labelSprite,
        startId: relationship.startId,
        endId: relationship.endId
      });
    }
  
    addGroundLightCircle(space_size) {
        if (isNaN(space_size)) {
            return;
        }

      const canvas = document.createElement('canvas');
      canvas.width = 1024;
      canvas.height = 1024;
      const context = canvas.getContext('2d');
  
      const gradient = context.createRadialGradient(
        canvas.width / 2, 
        canvas.height / 2, 
        0, 
        canvas.width / 2, 
        canvas.height / 2, 
        canvas.width / 2 
      );
  
      gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');   
      gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.5)'); 
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');   
  
      context.fillStyle = gradient;
      context.fillRect(0, 0, canvas.width, canvas.height);
  
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
  
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
        blending: THREE.AdditiveBlending,  
        side: THREE.DoubleSide,
        depthWrite: false
      });
  
      const radius = (space_size-5000) / 2; 
      const geometry = new THREE.CircleGeometry(radius, 64);
  
      const circle = new THREE.Mesh(geometry, material);
  
      circle.position.set(0, -space_size/2, 0);
      circle.rotation.x = -Math.PI / 2; 
  
      this.groundLightCircle = circle;  
      return circle;
    }
  
    updateGroundLightCircle(space_size) {
      if (this.groundLightCircle && !isNaN(space_size)) {
        this.groundLightCircle.position.set(0, -space_size/2, 0);
        
    
        const radius = (space_size-5000) / 2;
        this.groundLightCircle.geometry.dispose(); 
        this.groundLightCircle.geometry = new THREE.CircleGeometry(radius, 64);
      }
    }
  
    updateInfoPanel(data) {

      let html = `<div style="font-family: 'Segoe UI', Arial, sans-serif; color: #e0e0e0;">`;
      
    
      const headerColor = data.type === 'node' ? '#3498db' : '#e74c3c';
      const headerIcon = data.type === 'node' ? '●' : '↔';
      
      html += `
        <div style="background-color: ${headerColor}; padding: 8px 12px; border-radius: 4px 4px 0 0; 
                    margin-bottom: 10px; display: flex; align-items: center;">
          <span style="font-size: 18px; margin-right: 8px;">${headerIcon}</span>
          <h3 style="margin: 0; font-weight: bold; text-transform: capitalize;">${data.type}</h3>
        </div>`;
      
      if (data.type === 'node') {
       
        const labelList = data.labels.join(', ');
        
        // Get connections count from the nodes Map using the node's ID
        let connectionsCount = 0;
        if (this.nodes.has(data.id)) {
          connectionsCount = this.nodes.get(data.id).connections || 0;
        }
        
        html += `
          <div style="margin-bottom: 12px; background-color: rgba(52, 152, 219, 0.1); border-left: 3px solid #3498db; padding: 8px;">
            <div style="margin-bottom: 6px;"><strong>Labels:</strong> ${labelList}</div>
            <div style="margin-bottom: 6px;"><strong>ID:</strong> ${data.id}</div>
            <div><strong>Relationships:</strong> ${connectionsCount}</div>
          </div>`;
        
     
        if (data.properties && Object.keys(data.properties).length > 0) {
          html += `<div style="background-color: rgba(46, 204, 113, 0.1); border-left: 3px solid #2ecc71; padding: 8px;">
                    <h4 style="margin-top: 0; margin-bottom: 8px; color: #2ecc71;">Properties</h4>
                    <table style="width: 100%; border-collapse: collapse;">`;
                    
          for (const [key, value] of Object.entries(data.properties)) {
            html += `<tr>
                      <td style="padding: 3px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>${key}</strong></td>
                      <td style="padding: 3px; border-bottom: 1px solid rgba(255,255,255,0.1);">${value}</td>
                    </tr>`;
          }
          
          html += `</table></div>`;
        }
      } else if (data.type === 'relationship') {
        
        html += `
          <div style="margin-bottom: 12px; background-color: rgba(231, 76, 60, 0.1); border-left: 3px solid #e74c3c; padding: 8px;">
            <div style="margin-bottom: 6px;"><strong>Type:</strong> ${data.label || 'Undefined'}</div>
            <div style="margin-bottom: 6px;"><strong>ID:</strong> ${data.id}</div>
          </div>
          
          <div style="display: flex; margin-bottom: 10px;">
            <div style="flex: 1; background-color: rgba(52, 152, 219, 0.1); border-left: 3px solid #3498db; padding: 8px; cursor: pointer;"
                 onclick="objectManager.focusOnNode('${data.startId}')" 
                 onmouseover="this.style.backgroundColor='rgba(52, 152, 219, 0.3)'"
                 onmouseout="this.style.backgroundColor='rgba(52, 152, 219, 0.1)'">
              <h4 style="margin-top: 0; margin-bottom: 8px; color: #3498db;">From</h4>
              <div><strong>ID:</strong> ${data.startId}</div>
            </div>
            <div style="width: 20px; display: flex; justify-content: center; align-items: center;">→</div>
            <div style="flex: 1; background-color: rgba(52, 152, 219, 0.1); border-left: 3px solid #3498db; padding: 8px; cursor: pointer;"
                 onclick="objectManager.focusOnNode('${data.endId}')"
                 onmouseover="this.style.backgroundColor='rgba(52, 152, 219, 0.3)'"
                 onmouseout="this.style.backgroundColor='rgba(52, 152, 219, 0.1)'">
              <h4 style="margin-top: 0; margin-bottom: 8px; color: #3498db;">To</h4>
              <div><strong>ID:</strong> ${data.endId}</div>
            </div>
          </div>`;
      }
      
      // Close the container div
      html += `</div>`;
      
     
      const closeButton = `
        <button class="btn" 
          style="position: absolute; top: 8px; right: 8px; padding: 4px 8px; 
                font-size: 12px; background-color: rgba(0,0,0,0.4); color: #fff; 
                border: none; border-radius: 3px; cursor: pointer; transition: background-color 0.2s;"
          onmouseover="this.style.backgroundColor='rgba(255,0,0,0.4)'"
          onmouseout="this.style.backgroundColor='rgba(0,0,0,0.4)'"
          onclick="clearSelection()">✕</button>`;
      
      html += closeButton;
      
      this.infoPanel.innerHTML = html;
      
   
      this.infoPanel.style.top = "50%";
      this.infoPanel.style.transform = "translateY(-50%)";
    }
  
    clearSelection() {
      if (this.selectedObject) {
        this.resetObjectHighlight(this.selectedObject);
        this.selectedObject = null;
      }
      this.infoPanel.style.display = 'none';
    }
  
    checkHover() {

        if (this.selectedObject) return;
        
        const mouse = cameraController.getMouseCoordinates();
        
        raycaster.setFromCamera(mouse, camera);
        
        
        const objects = [...this.nodeObjects.values(), ...this.lineObjects];
        const intersects = raycaster.intersectObjects(objects);
        
        if (intersects.length > 0) {
        const object = intersects[0].object;
        
        if (this.hoveredObject !== object) {
          
            if (this.hoveredObject) {
                if (this.hoveredObject.userData.type === 'node') {
                    this.hoveredObject.material.emissiveIntensity = 0.7;
                    this.hoveredObject.scale.set(1, 1, 1);
                } else {
                    this.hoveredObject.material.opacity = 0.6;
                }
            }
        
            if (object.userData.type === 'node') {
                object.material.emissiveIntensity = 1.5;
                object.scale.set(1.1, 1.1, 1.1);
            } else {
                object.material.opacity = 1.0;
            }
            
            this.updateInfoPanel(object.userData);
            
            this.hoveredObject = object;
        }
        
        this.infoPanel.style.display = 'block';
        } else {
        
        if (this.hoveredObject) {
            if (this.hoveredObject.userData.type === 'node') {
                this.hoveredObject.material.emissiveIntensity = 0.7;
                this.hoveredObject.scale.set(1, 1, 1);
            } else {
                this.hoveredObject.material.opacity = 0.6;
            }
            
            this.hoveredObject = null;
            this.infoPanel.style.display = 'none';
        }
        }
        }
  
    handleClick(mouseCoordinates) {
      this.raycaster.setFromCamera(mouseCoordinates, this.camera);
  
      const objects = [...this.nodeObjects.values(), ...this.lineObjects];
      const intersects = this.raycaster.intersectObjects(objects);
  
      if (intersects.length > 0) {
        const object = intersects[0].object;
        
        // First reset the previous selection
        if (this.selectedObject && this.selectedObject !== object) {
          this.resetObjectHighlight(this.selectedObject);
        }
  
        this.selectedObject = object;
  
        if (object.userData.type === 'node') {
          this.highlightNode(object);
        } else {
          this.highlightRelationship(object);
        }
  
        // Reset any hover that isn't the selected object
        if (this.hoveredObject && this.hoveredObject !== this.selectedObject) {
          this.resetObjectHighlight(this.hoveredObject);
          this.hoveredObject = null;
        }
  
        this.updateInfoPanel(object.userData);
        this.infoPanel.style.display = 'block';
      } else {
        if (this.selectedObject) {
          this.resetObjectHighlight(this.selectedObject);
          this.selectedObject = null;
        }
        this.infoPanel.style.display = 'none';
      }
    }
  
    highlightNode(node) {
      if (!node || !node.material) return;
      
      const originalColor = node.userData.originalColor || node.material.color.getHex();
      node.userData.originalColor = originalColor;
      
      // Only store emissive properties if the material supports it
      if (node.material.emissive) {
        node.userData.originalEmissive = node.material.emissive.getHex();
        node.userData.originalEmissiveIntensity = node.material.emissiveIntensity || 0.5;
      }
      
      // Store original materials if we have children (for complex nodes)
      if (node.children && node.children.length > 0) {
        node.userData.childrenOriginalMaterials = [];
        node.children.forEach((child, index) => {
          if (child.material) {
            node.userData.childrenOriginalMaterials[index] = {
              color: child.material.color ? child.material.color.getHex() : 0xffffff
            };
            
            // Only store emissive properties if the material supports it
            if (child.material.emissive) {
              node.userData.childrenOriginalMaterials[index].emissive = 
                child.material.emissive.getHex();
              node.userData.childrenOriginalMaterials[index].emissiveIntensity = 
                child.material.emissiveIntensity || 0.5;
            }
            
            // Apply highlight effect to child material
            if (child.material.emissive) {
              child.material.emissive.setHex(0xffffff);
              child.material.emissiveIntensity = 1.5;
            } else {
              // For materials without emissive, modify color instead
              child.material.color.setHex(0xffffff);
            }
          }
        });
      }
      
      // Apply highlight effect to main material
      if (node.material.emissive) {
        node.material.emissive.setHex(0xffffff);
        node.material.emissiveIntensity = 1.5;
      } else {
        // For materials without emissive, modify color instead
        node.material.color.setHex(0xffffff);
      }
    }
  
    highlightRelationship(line) {
      if (!line || !line.material) return;
      
      line.userData.originalColor = line.material.color.getHex();
      line.userData.originalOpacity = line.material.opacity;
      
      line.material.color.setHex(0xffffff);
      line.material.opacity = 0.8;
    }
  
    resetObjectHighlight(object) {
      if (!object || !object.material) return;
      
      if (object.userData.type === 'node') {
      
        if (object.material.emissive && object.userData.originalEmissive !== undefined) {
          object.material.emissive.setHex(object.userData.originalEmissive);
        }
        if (object.userData.originalEmissiveIntensity !== undefined && object.material.emissive) {
          object.material.emissiveIntensity = object.userData.originalEmissiveIntensity;
        }
        
      
        if (object.userData.originalColor !== undefined) {
          object.material.color.setHex(object.userData.originalColor);
        }
        
       
        if (object.userData.childrenOriginalMaterials && object.children) {
          object.children.forEach((child, index) => {
            const originalMaterial = object.userData.childrenOriginalMaterials[index];
            if (child.material && originalMaterial) {
      
              if (originalMaterial.color !== undefined) {
                child.material.color.setHex(originalMaterial.color);
              }
              
             
              if (child.material.emissive && originalMaterial.emissive !== undefined) {
                child.material.emissive.setHex(originalMaterial.emissive);
              }
              if (originalMaterial.emissiveIntensity !== undefined && child.material.emissive) {
                child.material.emissiveIntensity = originalMaterial.emissiveIntensity;
              }
            }
          });
        }
      } else if (object.userData.type === 'relationship') {
        if (object.userData.originalColor !== undefined) {
          object.material.color.setHex(object.userData.originalColor);
        }
        if (object.userData.originalOpacity !== undefined) {
          object.material.opacity = object.userData.originalOpacity;
        }
      }
    }
  
    updateLabels() {
     
      if (this.useLOD) {
        for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
          const nodeData = this.nodes.get(nodeId);
          if (nodeData) {
            this.updateNodeLOD(nodeObject, nodeData, this.camera.position);
          }
        }
      }
    
 
      for (const [nodeId, label] of this.nodeLabels.entries()) {
        const node = this.nodeObjects.get(nodeId);
        if (node && node.visible) {
          label.lookAt(this.camera.position);
          
          const distance = this.camera.position.distanceTo(node.position);
          
          let scale = 1;
          
          if (distance > 5000) {
            scale = 1;
          } else if (distance > 2500) {
            const progress = (5000 - distance) / 2500; 
            scale = 0.1 + (5 * progress); 
          } else if (distance > 100) {
            const progress = (2500 - distance) / 2000; 
            scale = 5 - (4 * progress); 
          } else {
            scale = 1;
          }
          
          label.scale.set(200 * scale, 50 * scale, 1);
          label.visible = distance <= this.maxVisibleDistance;
        } else if (node && !node.visible) {
          label.visible = false;
        }
      }
      
     
      for (let i = 0; i < this.lineLabels.length; i++) {
        const labelInfo = this.lineLabels[i];
        const relLine = i < this.lineObjects.length ? this.lineObjects[i] : null;
        
      
        if (relLine && relLine.visible) {
          const startNode = this.nodeObjects.get(labelInfo.startId);
          const endNode = this.nodeObjects.get(labelInfo.endId);
      
          if (startNode && endNode) {
      
            const startPos = startNode.position;
            const endPos = endNode.position;
            
          
            const midPoint = new THREE.Vector3().addVectors(startPos, endPos).multiplyScalar(0.5);
            midPoint.y += 20; 
            
            labelInfo.sprite.position.copy(midPoint);
            labelInfo.sprite.lookAt(this.camera.position);
            
            const distance = this.camera.position.distanceTo(midPoint);
            
            let scale = 1; 
            
            if (distance > 5000) {
              scale = 1;
            } else if (distance > 2500) {
              const progress = (5000 - distance) / 2500; 
              scale = 0.1 + (2 * progress); 
            } else if (distance > 100) {
              const progress = (2500 - distance) / 2000; 
              scale = 2 - (1 * progress); 
            } else {
              scale = 1;
            }
            
            labelInfo.sprite.scale.set(200 * scale, 50 * scale, 1);
            labelInfo.sprite.visible = true;
          } else {
          
            labelInfo.sprite.visible = false;
          }
        } else {
      
          labelInfo.sprite.visible = false;
        }
      }
    }
  
    setupInstancedRendering() {
      
      if (this.instancedNodes) {
        this.scene.remove(this.instancedNodes);
        this.instancedNodes.geometry.dispose();
        this.instancedNodes.material.dispose();
        this.instancedNodes = null;
      }
      
     
      if (this.nodeObjects.size === 0 || !this.disableNiceMeshes) {
        return;
      }
      
      const nodeCount = this.nodeObjects.size;
      
   
      const geometry = new THREE.SphereGeometry(30, 8, 6);
      const material = new THREE.MeshStandardMaterial({
        metalness: 0.3,
        roughness: 0.7
      });
      
      const instancedMesh = new THREE.InstancedMesh(
        geometry,
        material,
        nodeCount
      );
      
      let index = 0;
      const tempMatrix = new THREE.Matrix4();
      const tempColor = new THREE.Color();
      
  
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(nodeId);
        if (nodeData) {
          const primaryLabel = nodeData.labels[0] || `Node ${nodeId}`;
          const color = this.getColorForLabel(primaryLabel);
          
          tempMatrix.setPosition(
            nodeData.position.x,
            nodeData.position.y,
            nodeData.position.z
          );
          
          tempColor.set(color);
          
          instancedMesh.setMatrixAt(index, tempMatrix);
          instancedMesh.setColorAt(index, tempColor);
          
          index++;
        }
      }
      
      instancedMesh.instanceMatrix.needsUpdate = true;
      if (instancedMesh.instanceColor) {
        instancedMesh.instanceColor.needsUpdate = true;
      }
      
      this.instancedNodes = instancedMesh;
      this.scene.add(instancedMesh);
    }
  
    setPerformanceMode(enabled) {
      console.log('setPerformanceMode', enabled);
      if (enabled && !this.isPerformanceModeEnabled) {
        
        this.setupInstancedRendering();
        
        if (this.instancedNodes && this.disableNiceMeshes) {
       
          for (const nodeObject of this.nodeObjects.values()) {
            nodeObject.visible = false;
          }
          
          this.instancedNodes.visible = true;
        } else {
         
          this.applyPerformanceMaterials();
        }
        
        this.maxVisibleDistance = 15000;
        this.isPerformanceModeEnabled = true;
        
      } else if (!enabled && this.isPerformanceModeEnabled) {
       
        if (this.instancedNodes) {
          this.instancedNodes.visible = false;
        }
        
        for (const nodeObject of this.nodeObjects.values()) {
          nodeObject.visible = true;
        }
        
       
        if (window.currentQualityMode === 'quality') {
          this.applyQualityMaterials(window.renderManager?.envMap);
        } else {
          this.applyStandardMaterials();
        }
    
        this.maxVisibleDistance = 50000;
        this.isPerformanceModeEnabled = false;
      }
    }
  
    createVisualization(nodes, relationships) {
      this.nodes = nodes;
      this.relationships = relationships;
      
      const batchSize = 50;
      let nodeCount = nodes.size;
      let processedCount = 0;
      const loadingIndicator = this.loadingIndicator;
      
      const createNodesInBatches = () => {
        const nodesToProcess = Array.from(nodes.entries())
          .slice(processedCount, processedCount + batchSize);
        
        nodesToProcess.forEach(([id, nodeData]) => {
          this.createNode(id, nodeData);
          processedCount++;
        });
        
        loadingIndicator.textContent = `Lade Nodes: ${processedCount}/${nodeCount}`;
        
        if (processedCount < nodeCount) {
          setTimeout(createNodesInBatches, 10);
        } else {
          createRelationshipsInBatches();
        }
      };
    
      const createRelationshipsInBatches = () => {
        const totalRelationships = relationships.length;
        let processedRelationships = 0;
        
        const processBatch = () => {
          const batchSize = 50;
          const relToProcess = relationships.slice(
            processedRelationships, 
            processedRelationships + batchSize
          );
          
          relToProcess.forEach(rel => {
            this.createRelationship(rel);
            processedRelationships++;
          });
          
          loadingIndicator.textContent = `Lade Beziehungen: ${processedRelationships}/${totalRelationships}`;
          
          if (processedRelationships < totalRelationships) {
            setTimeout(processBatch, 10);
          } else {
            loadingIndicator.textContent = `Visualisierung komplett: ${nodeCount} Nodes, ${totalRelationships} Beziehungen`;
            setTimeout(() => {
              loadingIndicator.style.opacity = '0.5';
            }, 3000);
          }
        };
        
        processBatch();
      };
      
      createNodesInBatches();
    }

    setDynamicRendering(enabled) {
      this.dynamicRendering = enabled;
      
      if (enabled) {
        this.updateDynamicNodeVisibility();
      } else {
       
        for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
          nodeObject.visible = true;
          const label = this.nodeLabels.get(nodeId);
          if (label) label.visible = true;
        }
      }
    }
    
    updateDynamicNodeVisibility() {
      if (!this.dynamicRendering) return;
      
    
      if (!this._frustum) {
        this._frustum = new THREE.Frustum();
        this._projScreenMatrix = new THREE.Matrix4();
      }
      
      this._projScreenMatrix.multiplyMatrices(
        this.camera.projectionMatrix,
        this.camera.matrixWorldInverse
      );
      this._frustum.setFromProjectionMatrix(this._projScreenMatrix);
      
     
      const visibleNodes = new Set();
      const nodesToUpdate = [];
      const labelsToUpdate = [];
      
     
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const isInFrustum = this._frustum.containsPoint(nodeObject.position);
        const distance = this.camera.position.distanceTo(nodeObject.position);
        const isVisible = isInFrustum && distance <= this.maxVisibleDistance;
        
        if (isVisible !== nodeObject.visible) {
          nodesToUpdate.push({ node: nodeObject, visible: isVisible, nodeId: nodeId });
        }
        
        if (isVisible) {
          visibleNodes.add(nodeId);
        }
      }
      
    
      for (const update of nodesToUpdate) {
        update.node.visible = update.visible;
        
      
        if (update.visible && 
            window.renderManager && 
            window.currentQualityMode === 'quality' &&
            !update.node.userData.qualityApplied) {
          const nodeData = this.nodes.get(update.nodeId);
          if (nodeData) {
            this.applyNodeQualityEffects(update.node, nodeData);
          }
        }
      }
      
     
      for (const [nodeId, label] of this.nodeLabels.entries()) {
        const isVisible = visibleNodes.has(nodeId);
        if (label.visible !== isVisible) {
          labelsToUpdate.push({ label, visible: isVisible });
        }
      }
      
      for (const update of labelsToUpdate) {
        update.label.visible = update.visible;
      }
      

      this.updateRelationshipVisibility(visibleNodes);
    }
    
    updateRelationshipVisibility(visibleNodes) {
      const linesToUpdate = [];
      
      for (let i = 0; i < this.lineObjects.length; i++) {
        const line = this.lineObjects[i];
        const startNodeId = line.userData.startId;
        const endNodeId = line.userData.endId;
        
     
        const atLeastOneNodeVisible = visibleNodes.has(startNodeId) || visibleNodes.has(endNodeId);
        
        let isInFrustum = atLeastOneNodeVisible;
        

        if (!atLeastOneNodeVisible && this._frustum) {
          const startNode = this.nodeObjects.get(startNodeId);
          const endNode = this.nodeObjects.get(endNodeId);
          
          if (startNode && endNode) {
        
            const lineStart = startNode.position;
            const lineEnd = endNode.position;
            
      
            isInFrustum = this._frustum.containsPoint(lineStart) || 
                          this._frustum.containsPoint(lineEnd) ||
                          
                          this._frustum.containsPoint(
                            new THREE.Vector3().addVectors(lineStart, lineEnd).multiplyScalar(0.5)
                          );
          }
        }
        
        const shouldBeVisible = isInFrustum;
        
        if (line.visible !== shouldBeVisible) {
          linesToUpdate.push({ line, visible: shouldBeVisible, index: i });
        }
      }
    
    
      for (const update of linesToUpdate) {
        update.line.visible = update.visible;
        
        if (update.index < this.lineLabels.length) {
         
          this.lineLabels[update.index].sprite.visible = update.visible;
        }
      }
    }
   
    

    getPerformanceIsEnabled() {
      return this.isPerformanceModeEnabled;
    }

    applyQualityMaterials(envMap) {
      
      if (window.renderManager) {
        window.currentQualityMode = 'quality';
      }
      
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) continue;
        
        
        nodeObject.userData.qualityApplied = false;
        
        
        const primaryLabel = nodeData.labels[0] || `Node ${nodeId}`;
        const color = this.getColorForLabel(primaryLabel);
        
       
        if (nodeObject.userData.atmosphereLayers) {
          for (const layer of nodeObject.userData.atmosphereLayers) {
            if (layer && layer.parent === nodeObject) {
              if (layer.material) layer.material.dispose();
              if (layer.geometry) layer.geometry.dispose();
              nodeObject.remove(layer);
            }
          }
          nodeObject.userData.atmosphereLayers = [];
        }
        
        if (nodeObject.userData.cloudMesh) {
          nodeObject.remove(nodeObject.userData.cloudMesh);
          if (nodeObject.userData.cloudMesh.material) {
            nodeObject.userData.cloudMesh.material.dispose();
          }
          if (nodeObject.userData.cloudMesh.geometry) {
            nodeObject.userData.cloudMesh.geometry.dispose();
          }
          nodeObject.userData.cloudMesh = null;
        }
        
     
        if (nodeObject.material) {
          nodeObject.material.dispose();
        }
        
        
        const nodeRadius = nodeObject.geometry.parameters?.radius || 30;
        
        // Create planetary surface material with enhanced features based on LOD
        if (nodeObject.userData.currentLOD === 'far') {
          nodeObject.material = new THREE.MeshPhysicalMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            metalness: 0.7,
            roughness: 0.4,
            envMap: envMap,
            envMapIntensity: 0.8,
            clearcoat: 0.3,
            clearcoatRoughness: 0.2,
            reflectivity: 0.5
          });
          this.addAtmosphericEffects(nodeObject, color, nodeRadius);
          this.addCloudLayer(nodeObject, color, envMap);
        }
        else if (nodeObject.userData.currentLOD === 'medium') {
          nodeObject.material = new THREE.MeshPhysicalMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            metalness: 0.7,
            roughness: 0.4,
            envMap: envMap,
            envMapIntensity: 0.8,
            clearcoat: 0.4,
            clearcoatRoughness: 0.3,
            reflectivity: 0.6
          });
          this.addAtmosphericEffects(nodeObject, color, nodeRadius);
          this.addCloudLayer(nodeObject, color, envMap);
        }
        else { 
          
          
          // First, clear any existing children
          while (nodeObject.children.length > 0) {
            const child = nodeObject.children[0];
            if (child.material) child.material.dispose();
            if (child.geometry) child.geometry.dispose();
            nodeObject.remove(child);
          }
          
          if (nodeObject.geometry) nodeObject.geometry.dispose();
          
          const innerSize = nodeRadius * 0.8;
          const outerSize = nodeRadius;
          
          const innerGeometry = new THREE.SphereGeometry(innerSize, 32, 32);
          const innerMaterial = new THREE.MeshPhysicalMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.4,
            metalness: 0.8,
            roughness: 0.3,
            envMap: envMap,
            envMapIntensity: 0.9,
            clearcoat: 0.7,
            clearcoatRoughness: 0.2,
            reflectivity: 0.8
          });
  
          const innerMesh = new THREE.Mesh(innerGeometry, innerMaterial);
          innerMesh.position.set(0, 0, 0);
          
          const outerGeometry = new THREE.SphereGeometry(outerSize, 32, 32);
          const outerMaterial = new THREE.MeshPhysicalMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            transparent: true,
            opacity: 0.6,
            metalness: 0.7,
            roughness: 0.4,
            envMap: envMap,
            envMapIntensity: 0.7,
            clearcoat: 0.5,
            clearcoatRoughness: 0.3,
            reflectivity: 0.7
          });
  
          nodeObject.geometry = outerGeometry;
          nodeObject.material = outerMaterial;
          nodeObject.add(innerMesh);
          
          
          this.addAtmosphericEffects(nodeObject, color, nodeRadius);
          this.addCloudLayer(nodeObject, color, envMap);
        }
        
       
        nodeObject.userData.qualityApplied = true;
      }
      
     
      if (!this._cloudTextureCache) {
        this._cloudTextureCache = this.generateCloudTexture();
      }
    }
    
    applyStandardMaterials() {
     
      if (window.renderManager) {
        window.currentQualityMode = 'standard';
      }
      
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) continue;
        
        
        nodeObject.userData.qualityApplied = false;
        
      
        if (nodeObject.userData.glowMesh) {
          nodeObject.userData.glowMesh.visible = false;
        }
        
      
        if (nodeObject.userData.atmosphereLayers) {
          if (nodeObject.userData.atmosphereLayers.length > 1) {
            for (let i = 1; i < nodeObject.userData.atmosphereLayers.length; i++) {
              const layer = nodeObject.userData.atmosphereLayers[i];
              if (layer && layer.parent === nodeObject) {
                if (layer.material) layer.material.dispose();
                if (layer.geometry) layer.geometry.dispose();
                nodeObject.remove(layer);
              }
            }
            
       
            nodeObject.userData.atmosphereLayers = nodeObject.userData.atmosphereLayers.slice(0, 1);
          }
        }
        
        if (nodeObject.userData.cloudMesh) {
          nodeObject.remove(nodeObject.userData.cloudMesh);
          if (nodeObject.userData.cloudMesh.material) {
            nodeObject.userData.cloudMesh.material.dispose();
          }
          if (nodeObject.userData.cloudMesh.geometry) {
            nodeObject.userData.cloudMesh.geometry.dispose();
          }
          nodeObject.userData.cloudMesh = null;
        }
        
      
        const primaryLabel = nodeData.labels[0] || `Node ${nodeId}`;
        const color = this.getColorForLabel(primaryLabel);
        const baseSize = 20 + Math.min(70, nodeData.connections * 5);
        
       
        if (nodeObject.userData.currentLOD === 'close') {
          
          this.applyCloseLOD(nodeObject, nodeData, baseSize, false);
        } 
        else if (nodeObject.userData.currentLOD === 'medium') {
          this.applyMediumLOD(nodeObject, nodeData, baseSize, false);
        }
        else {
          
          this.applyFarLOD(nodeObject, nodeData, baseSize, false);
        }
      }
    }
    
    applyPerformanceMaterials() {
      if (window.renderManager) {
        window.currentQualityMode = 'performance';
      }
      
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData) continue;
        
      
        nodeObject.userData.qualityApplied = false;
        
       
        this.cleanupQualityEffects(nodeObject);
        
        
        while (nodeObject.children.length > 0) {
          const child = nodeObject.children[0];
          if (child.material) child.material.dispose();
          if (child.geometry) child.geometry.dispose();
          nodeObject.remove(child);
        }
        
        
        const primaryLabel = nodeData.labels[0] || `Node ${nodeId}`;
        const color = this.getColorForLabel(primaryLabel);
        const baseSize = 20 + Math.min(70, nodeData.connections * 5);
        
     
        if (nodeObject.geometry) nodeObject.geometry.dispose();
        if (nodeObject.material) nodeObject.material.dispose();
        
      
        let geometry;
        if (nodeObject.userData.currentLOD === 'far') {
          // Far LOD uses tetrahedron (4 faces)
          geometry = new THREE.TetrahedronGeometry(baseSize * 0.7, 0);
        } else if (nodeObject.userData.currentLOD === 'medium') {
          // Medium LOD uses octahedron (8 faces)
          geometry = new THREE.OctahedronGeometry(baseSize * 0.7, 0);
        } else {
          // Close LOD uses icosahedron (20 faces)
          geometry = new THREE.IcosahedronGeometry(baseSize * 0.7, 0);
        }
        
        nodeObject.geometry = geometry;
        
     
        nodeObject.material = new THREE.MeshBasicMaterial({
          color: color,
          flatShading: true
        });
        
  
        nodeObject.visible = true;
      }
    }
    
    enableEdgeGlow(enabled) {
      this.edgeGlowEnabled = enabled;
      
      for (const line of this.lineObjects) {
        if (enabled) {
          if (!line.userData.glowLine) {
          
            const startNode = this.nodeObjects.get(line.userData.startId);
            const endNode = this.nodeObjects.get(line.userData.endId);
            
            if (!startNode || !endNode) continue;
            
         
            const points = line.geometry.attributes.position;
            const glowGeometry = new THREE.BufferGeometry().setFromPoints(
              Array(points.count).fill().map((_, i) => 
                new THREE.Vector3(
                  points.getX(i), 
                  points.getY(i), 
                  points.getZ(i)
                )
              )
            );
            
      
            const relationshipColor = 0x00ffff;
            
            const glowMaterial = new THREE.LineBasicMaterial({
              color: relationshipColor,
              transparent: true,
              opacity: 0.3,
              linewidth: 3
            });
            
            const glowLine = new THREE.Line(glowGeometry, glowMaterial);
            this.scene.add(glowLine);
            
            line.userData.glowLine = glowLine;
          } else {
            line.userData.glowLine.visible = true;
          }
        } else if (line.userData.glowLine) {
          line.userData.glowLine.visible = false;
        }
      }
    }
    
    focusOnNode(nodeId) {
      const nodeObject = this.nodeObjects.get(nodeId);
      if (nodeObject) {
        this.focusOnObject(nodeObject);
      }
    }
    
   
    focusOnObject(object) {
        if (!object) return;
        

        const targetPosition = object.position.clone();
        
      
        const offset = new THREE.Vector3(0, 20, 100);
        const cameraTargetPosition = targetPosition.clone().add(offset);
        
       
        if (window.cameraController) {
            window.cameraController.moveTo(cameraTargetPosition, targetPosition, 1000); 
        }
    }
    
    // Add this method to handle keypress navigation
    handleKeyNavigation(key) {
       
        if (key === 'f' || key === 'F') {
            if (this.selectedObject) {
                this.focusOnObject(this.selectedObject);
            }
        } else if (key === 'from' || key === 'arrowleft') {
            if (this.selectedObject && this.selectedObject.userData.type === 'relationship') {
                const startNode = this.nodeObjects.get(this.selectedObject.userData.startId);
                if (startNode) {
                    this.focusOnObject(startNode);
                }
            }
        } else if (key === 'to' || key === 'arrowright') {
            if (this.selectedObject && this.selectedObject.userData.type === 'relationship') {
                const endNode = this.nodeObjects.get(this.selectedObject.userData.endId);
                if (endNode) {
                    this.focusOnObject(endNode);
                }
            }
        }
    }

    cleanupNodeMeshResources(nodeObject) {
      // First remove all children that might have materials
      while (nodeObject.children.length > 0) {
        const child = nodeObject.children[0];
        
      
        if (child.geometry) child.geometry.dispose();
        
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach(material => {
              this.disposeMaterialResources(material);
            });
          } else {
            this.disposeMaterialResources(child.material);
          }
        }
        
        
        if (child.userData && child.userData.atmosphereLayers) {
          child.userData.atmosphereLayers.forEach(layer => {
            if (layer.geometry) layer.geometry.dispose();
            if (layer.material) this.disposeMaterialResources(layer.material);
          });
        }
        
        nodeObject.remove(child);
      }
      
     
      nodeObject.userData.atmosphereLayers = [];
      nodeObject.userData.cloudLayers = [];
      
     
      if (nodeObject.geometry) {
        
        const geometryParams = nodeObject.geometry.parameters;
        nodeObject.geometry.dispose();
        nodeObject.geometry = null;
        return geometryParams;
      }
      
      return null;
    }
    
    disposeMaterialResources(material) {
      if (!material) return;
      
      // Dispose textures
      for (const prop in material) {
        if (material[prop] && material[prop].isTexture) {
          material[prop].dispose();
        }
      }
      
      
      if (material.uniforms) {
        for (const key in material.uniforms) {
          if (material.uniforms[key].value && 
              material.uniforms[key].value.isTexture) {
            material.uniforms[key].value.dispose();
          }
        }
      }
      
      material.dispose();
    }

    applyNodeQualityEffects(nodeObject, nodeData) {
    
      const primaryLabel = nodeData.labels[0] || `Node ${nodeData.id}`;
      const color = this.getColorForLabel(primaryLabel);
      
    
      nodeObject.userData.qualityApplied = true;
      
     
      if (nodeObject.material) {
        if (window.renderManager && window.renderManager.envMap) {
          nodeObject.material.envMap = window.renderManager.envMap;
          nodeObject.material.envMapIntensity = 0.8;
          nodeObject.material.needsUpdate = true;
        }
    
        if (nodeObject.material.type === 'MeshStandardMaterial' || 
            nodeObject.material.type === 'MeshPhysicalMaterial') {
          nodeObject.material.metalness = 0.7;
          nodeObject.material.roughness = 0.4;
          nodeObject.material.emissive = new THREE.Color(color);
          nodeObject.material.emissiveIntensity = 0.3;
          
       
          if (nodeObject.material.type !== 'MeshPhysicalMaterial') {
            const oldMaterial = nodeObject.material;
            const newMaterial = new THREE.MeshPhysicalMaterial({
              color: oldMaterial.color.clone(),
              emissive: oldMaterial.emissive.clone(),
              emissiveIntensity: oldMaterial.emissiveIntensity,
              metalness: 0.7,
              roughness: 0.4,
              envMap: window.renderManager ? window.renderManager.envMap : null,
              envMapIntensity: 0.8,
              clearcoat: 0.6,
              clearcoatRoughness: 0.2,
              reflectivity: 0.8
            });
            nodeObject.material.dispose();
            nodeObject.material = newMaterial;
          }
        }
      }
      
     
      const nodeRadius = nodeObject.geometry.parameters?.radius || 30;
  
      if (nodeObject.userData.atmosphereLayers) {
        for (const layer of nodeObject.userData.atmosphereLayers) {
          if (layer && layer.parent === nodeObject) {
            if (layer.material) layer.material.dispose();
            if (layer.geometry) layer.geometry.dispose();
            nodeObject.remove(layer);
          }
        }
      }
      
      this.addAtmosphericEffects(nodeObject, color, nodeRadius);
      
      // Add or update cloud layer
      if (nodeObject.userData.cloudMesh) {
        nodeObject.remove(nodeObject.userData.cloudMesh);
        nodeObject.userData.cloudMesh.material.dispose();
        nodeObject.userData.cloudMesh.geometry.dispose();
        nodeObject.userData.cloudMesh = null;
      }
      
      this.addCloudLayer(nodeObject, color, window.renderManager ? window.renderManager.envMap : null);
    }
    
    addAtmosphericEffects(nodeObject, color, nodeRadius) {
     
      if (nodeObject.userData.atmosphereLayers) {
        for (const layer of nodeObject.userData.atmosphereLayers) {
          if (layer && layer.parent === nodeObject) {
            if (layer.material) layer.material.dispose();
            if (layer.geometry) layer.geometry.dispose();
            nodeObject.remove(layer);
          }
        }
      }
      
      const atmosphereLayers = [];
      
      // Add outer glow atmosphere
      const atmoGeometry = new THREE.SphereGeometry(nodeRadius * 1.3, 32, 32);
      const atmoMaterial = new THREE.MeshPhysicalMaterial({
        color: color,
        transparent: true,
        opacity: 0.15,
        side: THREE.BackSide,
        envMap: window.renderManager ? window.renderManager.envMap : null,
        envMapIntensity: 0.4,
        roughness: 1.0,
        metalness: 0.0,
        clearcoat: 0.0,
        transmission: 0.9,
        ior: 1.2
      });
      
      const atmosphereMesh = new THREE.Mesh(atmoGeometry, atmoMaterial);
      atmosphereMesh.userData.type = 'atmosphere';
      nodeObject.add(atmosphereMesh);
      atmosphereLayers.push(atmosphereMesh);
      
      // Add polar glow effect
      const polarGeometry = new THREE.RingGeometry(nodeRadius * 1.4, nodeRadius * 1.8, 32);
      const polarMaterial = new THREE.MeshBasicMaterial({
        color: new THREE.Color(color).multiplyScalar(1.5),
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending
      });
      
      const polarRing = new THREE.Mesh(polarGeometry, polarMaterial);
      polarRing.rotation.x = Math.PI / 2;
      polarRing.position.y = 0;
      polarRing.userData.type = 'polarRing';
      nodeObject.add(polarRing);
      atmosphereLayers.push(polarRing);
      
     
      nodeObject.userData.atmosphereLayers = atmosphereLayers;
      
      return atmosphereLayers;
    }
    
    addCloudLayer(nodeObject, color, envMap) {
      
      // Only add if not already present
      if (!nodeObject.userData.cloudMesh) {
        const nodeRadius = nodeObject.geometry.parameters?.radius || 30;
        const cloudGeometry = new THREE.SphereGeometry(nodeRadius * 1.05, 24, 24);
        const cloudMaterial = new THREE.MeshPhysicalMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: 0.4,
          alphaMap: this.getCloudTexture(),
          envMap: envMap,
          roughness: 1.0,
          metalness: 0.0,
          transmission: 0.2
        });
        
        const cloudMesh = new THREE.Mesh(cloudGeometry, cloudMaterial);
        cloudMesh.rotation.y = Math.random() * Math.PI * 2;
        cloudMesh.rotation.x = Math.random() * Math.PI * 0.2;
        cloudMesh.userData.type = 'cloudLayer';
        nodeObject.add(cloudMesh);
        nodeObject.userData.cloudMesh = cloudMesh;
        
        // Add cloud rotation animation data
        nodeObject.userData.cloudRotationSpeed = 0.0003 + Math.random() * 0.0005;
        nodeObject.userData.cloudRotationAxis = new THREE.Vector3(
          Math.random() * 0.2 - 0.1,
          1,
          Math.random() * 0.2 - 0.1
        ).normalize();
      }
    }

    updateQualityAnimations(time) {
     
      if (this.nodeObjects.size === 0) return;
    
     
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
       
        if (!nodeObject.userData.qualityApplied) continue;
        
   
        if (nodeObject.userData.atmosphereLayers) {
          for (const layer of nodeObject.userData.atmosphereLayers) {
            if (layer.userData.type === 'polarRing') {
          
              layer.rotation.z = time * 0.2;
            }
          }
        }
        
   
        if (nodeObject.userData.cloudMesh) {
         
          nodeObject.userData.cloudMesh.rotation.y = time * 0.05;
          
        
          const pulseFactor = 0.7 + Math.sin(time * 0.3) * 0.1;
          if (nodeObject.userData.cloudMesh.material) {
            nodeObject.userData.cloudMesh.material.opacity = 0.4 * pulseFactor;
          }
        }
      }
    }
    
    generateCloudTexture(color = 0xffffff) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 512;
      canvas.height = 512;
      
      
      ctx.fillStyle = 'rgba(0,0,0,0)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      
      const r = (color >> 16) & 255;
      const g = (color >> 8) & 255;
      const b = color & 255;
      
    
      const cloudColor = `rgba(${r}, ${g}, ${b}, 0.1)`;
      ctx.fillStyle = cloudColor;
      
   
      const numShapes = 50;
      for (let i = 0; i < numShapes; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const radius = 20 + Math.random() * 60;
        
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      }
      
    
      ctx.filter = 'blur(16px)';
      ctx.drawImage(canvas, 0, 0);
      ctx.filter = 'none';
      
     
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
      
      return texture;
    }

    getCloudTexture() {
      
      if (!this._cloudTextureCache) {
        this._cloudTextureCache = this.generateCloudTexture();
      }
      return this._cloudTextureCache;
    }

    forceApplyQualityToAllNodes() {
     
      const isQualityMode = window.currentQualityMode === 'quality';

      console.log(`wtf ${window.currentQualityMode}`);
      
      console.log(`Force applying quality mode to all nodes: ${isQualityMode ? 'quality' : 'standard'}`);
      
  
      for (const [nodeId, nodeObject] of this.nodeObjects.entries()) {
        const nodeData = this.nodes.get(nodeId);
        if (!nodeData || !nodeObject) continue;
        
       
        nodeObject.userData.qualityApplied = false;
        
      
        this.cleanupQualityEffects(nodeObject);
        
        
        const distance = this.camera.position.distanceTo(nodeObject.position);
        
        if (distance > 10000) {  // Far LOD threshold
          nodeObject.userData.currentLOD = 'far';
          this.applyFarLOD(nodeObject, nodeData, 20 + Math.min(70, nodeData.connections * 5), isQualityMode);
        } 
        else if (distance > 3000) {  // Medium LOD threshold
          nodeObject.userData.currentLOD = 'medium';
          this.applyMediumLOD(nodeObject, nodeData, 20 + Math.min(70, nodeData.connections * 5), isQualityMode);
        }
        else {  
          nodeObject.userData.currentLOD = 'close';
          this.applyCloseLOD(nodeObject, nodeData, 20 + Math.min(70, nodeData.connections * 5), isQualityMode);
        }
        
       
        if (isQualityMode) {
          this.applyNodeQualityEffects(nodeObject, nodeData);
          nodeObject.userData.qualityApplied = true;
        }
      }
    }
    
    
    cleanupQualityEffects(nodeObject) {
  
      if (nodeObject.userData.atmosphereLayers) {
        for (const layer of nodeObject.userData.atmosphereLayers) {
          if (layer && layer.parent === nodeObject) {
            if (layer.material) layer.material.dispose();
            if (layer.geometry) layer.geometry.dispose();
            nodeObject.remove(layer);
          }
        }
        nodeObject.userData.atmosphereLayers = [];
      }
      
      // Remove cloud mesh
      if (nodeObject.userData.cloudMesh) {
        nodeObject.remove(nodeObject.userData.cloudMesh);
        if (nodeObject.userData.cloudMesh.material) {
          nodeObject.userData.cloudMesh.material.dispose();
        }
        if (nodeObject.userData.cloudMesh.geometry) {
          nodeObject.userData.cloudMesh.geometry.dispose();
        }
        nodeObject.userData.cloudMesh = null;
      }
      
      // Remove any glitter particles or special effects
      for (let i = nodeObject.children.length - 1; i >= 0; i--) {
        const child = nodeObject.children[i];
        if (child.userData && 
           (child.userData.type === 'glitter' || 
            child.userData.type === 'atmosphere' || 
            child.userData.type === 'cloudLayer' ||
            child.userData.type === 'polarRing')) {
          
          if (child.material) child.material.dispose();
          if (child.geometry) child.geometry.dispose();
          nodeObject.remove(child);
        }
      }
    }
  }

