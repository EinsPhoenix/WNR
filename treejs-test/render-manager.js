// render-manager.js
class RenderManager {
    constructor(renderer, camera, scene) {
      this.renderer = renderer;
      this.camera = camera;
      this.scene = scene;
      this.composer = null;
      this.bloomPass = null;
      this.ssaoPass = null;
      this.loadingIndicator = document.getElementById('loading');
      this.disableAnimations = false;
      this.disableNiceMeshes = false;
      this.defaultFarPlane = 20000;
      this.renderDistanceController = null;
      this.spaceSize = 50000;
      this.useLOD = true;
      this.useInstancedRendering = false;
      this.lastFPSUpdate = 0;
      this.frameCount = 0;
      this.currentFPS = 0;
      this.fpsDisplay = document.createElement('div');
      this.setupFPSDisplay();
      this.envMap = null;
      this.qualityAnimationTime = 0;
      this.textureCache = new Map();
      this.cubemapCache = new Map();
      this.initProfiler();
      
    }
  
    init() {
      try {
        this.initProfiler();
        this.setupEffects();
        this.setupEnvironmentMap();
      } catch (error) {
        console.error("Konnte Effekte nicht initialisieren:", error);
        this.fallbackToBasicRenderer();
      }
  
      this.setupGUI();
      window.objectManager.setUseLOD(this.useLOD);
      
     
      this.applyQualityPreset('standard');
      
    
      window.addEventListener('beforeunload', () => this.dispose());
    }
    
    setupEnvironmentMap() {
      const intensity = 1.0;
      const colors = [
        new THREE.Color(0x0077ff).multiplyScalar(intensity),
        new THREE.Color(0xff0077).multiplyScalar(intensity),
        new THREE.Color(0x0000ff).multiplyScalar(intensity),
      ];
      
      this.envMap = this.getCachedCubemap('default', colors, intensity);
    }
    
    generateEnvironmentCubemap(colors, pmremGenerator) {
      const size = 256;
      const cubeRenderTarget = new THREE.WebGLCubeRenderTarget(size);
      const cubecam = new THREE.CubeCamera(1, 1000, cubeRenderTarget);
      
      const scene = new THREE.Scene();
      
   
      const geometry = new THREE.SphereGeometry(100, 32, 32);
      const material = new THREE.ShaderMaterial({
        uniforms: {
          color1: { value: colors[0] },
          color2: { value: colors[1] },
          color3: { value: colors[2] }
        },
        vertexShader: `
          varying vec3 vWorldPosition;
          void main() {
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 color1;
          uniform vec3 color2;
          uniform vec3 color3;
          varying vec3 vWorldPosition;
          
          void main() {
            vec3 viewDirection = normalize(vWorldPosition);
            float t = viewDirection.y * 0.5 + 0.5;
            float s = viewDirection.x * 0.5 + 0.5;
            vec3 color = mix(mix(color1, color2, s), color3, t);
            gl_FragColor = vec4(color, 1.0);
          }
        `,
        side: THREE.BackSide
      });
      
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      cubecam.update(this.renderer, scene);
      
      const result = pmremGenerator.fromCubemap(cubeRenderTarget.texture);
      
  
      geometry.dispose();
      material.dispose();
      scene.remove(mesh);
      
      return result;
    }

    getCachedTexture(key, createFunc) {
      if (!this.textureCache.has(key)) {
        const texture = createFunc();
        this.textureCache.set(key, texture);
      }
      return this.textureCache.get(key);
    }

    getCachedCubemap(key, colors, intensity) {
      const cacheKey = `${key}_${colors.map(c => c.getHexString()).join('_')}_${intensity}`;
      
      if (!this.cubemapCache.has(cacheKey)) {
        const pmremGenerator = new THREE.PMREMGenerator(this.renderer);
        pmremGenerator.compileEquirectangularShader();
        
        const cubeRenderTarget = this.generateEnvironmentCubemap(colors, pmremGenerator);
        this.cubemapCache.set(cacheKey, cubeRenderTarget.texture);
        
        // Clean up
        pmremGenerator.dispose();
      }
      
      return this.cubemapCache.get(cacheKey);
    }

    setupGUI() {
      const gui = new dat.GUI();
      const renderOptions = gui.addFolder('Render Optionen');
      const performanceOptions = gui.addFolder('Performance Optionen');

      const params = {
          renderQuality: 'Standard',
          renderDistance: this.defaultFarPlane,
          spaceSize: this.spaceSize,
          useLOD: this.useLOD,
          showFPS: true,
          dynamicRendering: true,
          bundlingStrength: 0.5,
          adaptivePerformance: true,
          performanceMode: false,
          enableProfiler: false
      };

      renderOptions.add(params, 'renderQuality', ['Qualität', 'Standard', 'Performance'])
          .name('Anzeigemodus')
          .onChange((value) => this.applyRenderOption(value));

      this.renderDistanceController = renderOptions.add(params, 'renderDistance', 1000, 1000000)
          .name('Renderdistanz')
          .onChange((value) => this.setRenderDistance(value));

      this.spaceSizeController = renderOptions.add(params, "spaceSize", 1000, 1000000)
         .name("Raumgröße")
         .onChange((value) => this.setSpaceSize(value));

      renderOptions.add(params, "showFPS")
          .name("FPS anzeigen")
          .onChange((value) => {
            this.fpsDisplay.style.display = value ? 'block' : 'none';
          });
          
      renderOptions.add(params, "dynamicRendering")
          .name("Dynamisches Rendering")
          .onChange((value) => {
            if (window.objectManager) {
              window.objectManager.setDynamicRendering(value);
            }
          });
          
    
          
     

     
      performanceOptions.add(params, "adaptivePerformance")
          .name("Adaptive Performance")
          .onChange((value) => {
            window.useAdaptivePerformance = value;
            this.updatePerformanceStatus();
          });
          
      this.performanceModeController = performanceOptions.add(params, "performanceMode")
          .name("Performance Modus")
          .onChange((value) => {
              if (window.objectManager) {
                  window.objectManager.setPerformanceMode(value);
              }
              this.updatePerformanceStatus();
          });

      performanceOptions.add(params, "enableProfiler")
          .name("Profiler aktivieren")
          .onChange((value) => {
            this.toggleProfiler(value);
          });

      renderOptions.open();
      performanceOptions.open();
      
      this.applyRenderOption(params.renderQuality);
      
      if (window.objectManager) {
        window.objectManager.setDynamicRendering(params.dynamicRendering);
      }
      
      window.useAdaptivePerformance = params.adaptivePerformance;
      if (window.objectManager) {
        window.objectManager.setPerformanceMode(params.performanceMode);
      }
      
      this.createPerformanceStatusDisplay();
      this.updatePerformanceStatus();
    }

    createPerformanceStatusDisplay() {
      this.performanceStatus = document.createElement('div');
      this.performanceStatus.style.position = 'absolute';
      this.performanceStatus.style.top = '40px';  
      this.performanceStatus.style.left = '5px';
      this.performanceStatus.style.color = 'white';
      this.performanceStatus.style.fontFamily = 'monospace';
      this.performanceStatus.style.zIndex = '1000';
      this.performanceStatus.style.backgroundColor = 'rgba(0,0,0,0.5)';
      this.performanceStatus.style.padding = '5px';
      this.performanceStatus.style.borderRadius = '3px';
      document.body.appendChild(this.performanceStatus);
    }

    updatePerformanceStatus() {
      if (!this.performanceStatus) return;
      
      const adaptiveMode = window.useAdaptivePerformance ? 'AN' : 'AUS';
      const performanceMode = window.objectManager && window.objectManager.getPerformanceIsEnabled() ? 'AN' : 'AUS';
      
      this.performanceStatus.innerHTML = 
          `Adaptive: <span style="color:${window.useAdaptivePerformance ? '#4CAF50' : '#F44336'}">${adaptiveMode}</span> | ` +
          `Perf-Modus: <span style="color:${performanceMode === 'AN' ? '#F44336' : '#4CAF50'}">${performanceMode}</span>`;
    }
     
    setRenderDistance(distance) {
      if (this.camera.far === distance) return; 
  
      this.camera.far = distance;
      this.camera.updateProjectionMatrix();
  
      if (this.scene.fog) {
          this.scene.fog.far = distance * 0.9;
      }
      
      if (this.renderDistanceController && this.renderDistanceController.getValue() !== distance) {
          this.renderDistanceController.setValue(distance);
      }
    }

    setSpaceSize(spaceSize) {
      this.spaceSize = spaceSize;
      this.updateEventBusHandler();
    }

    updateEventBusHandler() {
      if (window.eventBus) {
        window.eventBus.dispatchEvent(new CustomEvent('renderOptionChanged', {
          detail: {
            disableAnimations: this.disableAnimations,
            disableNiceMeshes: this.disableNiceMeshes,
            spaceSize: this.spaceSize,
            useLOD: this.useLOD
          }
        }));
      }
    }
    
    applyRenderOption(option) {
      switch(option) {
        case 'Qualität':
          window.currentQualityMode = 'quality';
          this.applyQualityPreset('quality');
          break;
        case 'Standard':
          window.currentQualityMode = 'standard';
          this.applyQualityPreset('standard');
          break;
        case 'Performance':
          window.currentQualityMode = 'performance';
          this.applyQualityPreset('performance');
          break;
      }
    }
    
    checkEffectsAvailability() {
      const availableEffects = {
        composer: typeof THREE.EffectComposer !== 'undefined',
        renderPass: typeof THREE.RenderPass !== 'undefined',
        bloomPass: typeof THREE.UnrealBloomPass !== 'undefined',
        ssaoPass: typeof THREE.SSAOPass !== 'undefined'
      };
      
    
      this.availableEffects = availableEffects;
      
      return availableEffects;
    }
    
    setupEffects() {
     
      const effects = this.checkEffectsAvailability();
      
      if (!effects.composer || !effects.renderPass) {
        console.warn("Basic post-processing is not available. Using standard renderer.");
        this.fallbackToBasicRenderer();
        return;
      }
      
      try {
        this.setupComposer();
        
        if (effects.bloomPass) {
          this.setupBloomEffect();
        } else {
          console.warn("Bloom effect not available. Some visual features will be disabled.");
        }
        
      
      } catch (error) {
        console.error("Failed to initialize effects:", error);
        this.fallbackToBasicRenderer();
      }
    }
    
    setupSSAO() {
      if (!this.composer || !this.availableEffects.ssaoPass) {
        console.warn('SSAO effect could not be initialized. Required dependencies missing.');
        return false;
      }
      
      if (this.ssaoPass) {
        this.ssaoPass.enabled = true;
        return true;
      }
      
      try {
        this.ssaoPass = new THREE.SSAOPass(
          this.scene, 
          this.camera, 
          window.innerWidth, 
          window.innerHeight
        );
        this.ssaoPass.kernelRadius = 16;
        this.ssaoPass.minDistance = 0.005;
        this.ssaoPass.maxDistance = 0.1;
        
        this.composer.addPass(this.ssaoPass);
        return true;
      } catch (error) {
        console.error("Error initializing SSAO effect:", error);
        return false;
      }
    }
  
    displayAllLabels(visible) {
      if (window.objectManager) {
        window.objectManager.nodeLabels.forEach(label => {
          label.visible = visible;
        });
        
        window.objectManager.lineLabels.forEach(labelInfo => {
          labelInfo.sprite.visible = visible;
        });
      }
    }
  
    setupBloomEffect() {
      if (!this.composer || typeof THREE.UnrealBloomPass === 'undefined') {
        console.warn('Bloom effect could not be initialized. Missing composer or UnrealBloomPass.');
        return false;
      }
      
      if (this.bloomPass) {
        return true; 
      }
      
      try {
        this.bloomPass = new THREE.UnrealBloomPass(
          new THREE.Vector2(window.innerWidth, window.innerHeight),
          0,    // Default to disabled
          0.6,  // Radius
          0.85  // Threshold
        );
        
        this.composer.addPass(this.bloomPass);
        return true;
      } catch (error) {
        console.error("Error initializing bloom effect:", error);
        return false;
      }
    }
  
    onWindowResize() {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      
      if (this.composer && this.composer.setSize) {
        try {
          this.composer.setSize(window.innerWidth, window.innerHeight);
        } catch (error) {
          console.error("Fehler beim Resize des Composers:", error);
        }
      }
      
      if (this.ssaoPass) {
        this.ssaoPass.setSize(window.innerWidth, window.innerHeight);
      }
    }
  
    render() {
      try {
        this.startProfiling('fullRender');
        
     
        if (!this.disableAnimations && window.currentQualityMode === 'quality' && window.objectManager) {
          this.startProfiling('animations');
          this.qualityAnimationTime += 0.01;
          window.objectManager.updateQualityAnimations(this.qualityAnimationTime);
          this.endProfiling('animations');
        }
        
      
        if (window.useAdaptivePerformance) {
          this.updateLODBasedOnPerformance();
        }
      
        this.startProfiling('rendering');
        if (this.composer && this.composer.renderer) {
          this.composer.render();
        } else {
          this.renderer.render(this.scene, this.camera);
        }
        this.endProfiling('rendering');
        
        this.updateFPS();
        this.endProfiling('fullRender');
        
      } catch (error) {
        console.error("Render error:", error);
      
        this.renderer.render(this.scene, this.camera);
      }
    }
  
    getDisableAnimations() {
      return this.disableAnimations;
    }
  
    getDisableNiceMeshes() {
      return this.disableNiceMeshes;
    }

    getRenderDistance() {
      return this.camera.far;
    }
      
    resetRenderDistance() {
      this.setRenderDistance(this.defaultFarPlane);
    }

    setupFPSDisplay() {
      this.fpsDisplay.style.position = 'absolute';
      this.fpsDisplay.style.top = '5px';
      this.fpsDisplay.style.left = '5px';
      this.fpsDisplay.style.color = 'white';
      this.fpsDisplay.style.fontFamily = 'monospace';
      this.fpsDisplay.style.zIndex = '1000';
      this.fpsDisplay.style.backgroundColor = 'rgba(0,0,0,0.5)';
      this.fpsDisplay.style.padding = '5px';
      this.fpsDisplay.style.borderRadius = '3px';
      document.body.appendChild(this.fpsDisplay);
    }

 
    updateFPS() {
      this.frameCount++;
      const now = performance.now();
      
    
      if (now - this.lastFPSUpdate > 1000) {
        this.currentFPS = Math.round((this.frameCount * 1000) / (now - this.lastFPSUpdate));
        this.fpsDisplay.textContent = `FPS: ${this.currentFPS}`;
        this.frameCount = 0;
        this.lastFPSUpdate = now;
      }
    }

    dispose() {
      // Dispose environment map resources
      if (this.envMap) {
        this.envMap.dispose();
      }
      
      // Dispose bloom effect
      if (this.bloomPass) {
        this.bloomPass.dispose();
      }
      
      // Dispose SSAO effect
      if (this.ssaoPass) {
        this.ssaoPass.dispose();
      }
      
      // Clean up composer
      if (this.composer) {
        this.composer.dispose();
      }
      
      // Remove DOM elements
      if (this.fpsDisplay && this.fpsDisplay.parentNode) {
        this.fpsDisplay.parentNode.removeChild(this.fpsDisplay);
      }
      
      if (this.performanceStatus && this.performanceStatus.parentNode) {
        this.performanceStatus.parentNode.removeChild(this.performanceStatus);
      }
      
     
      this.envMap = null;
      this.bloomPass = null;
      this.ssaoPass = null;
      this.composer = null;
    }

    setupComposer() {
      if (typeof THREE.EffectComposer === 'undefined' || 
          typeof THREE.RenderPass === 'undefined') {
        console.warn('Effect Composer could not be initialized. Required dependencies missing.');
        return false;
      }
      
      this.composer = new THREE.EffectComposer(this.renderer);
      
      const renderPass = new THREE.RenderPass(this.scene, this.camera);
      this.composer.addPass(renderPass);
      
      return true;
    }
    
    fallbackToBasicRenderer() {
      this.composer = null;
      this.bloomPass = null;
      this.ssaoPass = null;
      
      console.warn("Falling back to basic renderer without post-processing effects");
    }

    configureLOD(enabled, settings = {}) {
      this.useLOD = enabled;
      
      if (window.objectManager) {
        window.objectManager.setUseLOD(enabled);
        
      
        if (settings.bias && typeof window.objectManager.setLODBias === 'function') {
          window.objectManager.setLODBias(settings.bias);
        }
      }
      
     
      this.lodSettings = {
        enabled: enabled,
        thresholds: settings.thresholds || [5000, 15000, 30000],
        bias: settings.bias || 1.0,
        transitionDuration: settings.transitionDuration || 0.5
      };
    }
    
    updateLODBasedOnPerformance() {
    
      if (!window.objectManager || !this.useLOD || this.currentFPS <= 0 || window.currentQualityMode == "performance") return;
      
   
      let performanceLevel = 'normal';
      
      if (this.currentFPS < 10) {
        performanceLevel = 'low';
       
        if (!this.lastPerformanceLevel || this.lastPerformanceLevel !== 'low') {
          
          if (window.objectManager.isPerformanceModeEnabled !== true) {
            window.objectManager.setPerformanceMode(true);
          }
        }
      } else if (this.currentFPS > 100) {
        performanceLevel = 'high';
        
        if (this.lastPerformanceLevel === 'low') {
        
          if (window.objectManager.isPerformanceModeEnabled === true) {
            window.objectManager.setPerformanceMode(false);
          }
        }
      }
      
      
      this.lastPerformanceLevel = performanceLevel;
      
    
      if (typeof window.objectManager.updateNodeLODs === 'function') {
        window.objectManager.updateNodeLODs();
      }
    }

    initProfiler() {
      this.profiler = {
        active: false,
        metrics: {},
        lastUpdate: 0,
        updateInterval: 500,
        history: {}
      };
    }

    startProfiling(name) {
      if (!this.profiler.active) return;
      
      if (!this.profiler.metrics[name]) {
        this.profiler.metrics[name] = { start: 0, time: 0, count: 0 };
      }
      
      this.profiler.metrics[name].start = performance.now();
    }

    endProfiling(name) {
      if (!this.profiler.active || !this.profiler.metrics[name]) return;
      
      const metric = this.profiler.metrics[name];
      const duration = performance.now() - metric.start;
      
      metric.time += duration;
      metric.count++;
      
      // Update history periodically
      const now = performance.now();
      if (now - this.profiler.lastUpdate > this.profiler.updateInterval) {
        this.updateProfilingHistory();
        this.profiler.lastUpdate = now;
      }
    }

    updateProfilingHistory() {
      Object.keys(this.profiler.metrics).forEach(name => {
        const metric = this.profiler.metrics[name];
        
        if (!this.profiler.history[name]) {
          this.profiler.history[name] = [];
        }
        
        if (metric.count > 0) {
          const avgTime = metric.time / metric.count;
          this.profiler.history[name].push({
            time: performance.now(),
            value: avgTime
          });
          
        
          if (this.profiler.history[name].length > 100) {
            this.profiler.history[name].shift();
          }
          
        
          metric.time = 0;
          metric.count = 0;
        }
      });
      
      this.updatePerformanceDisplay();
    }

    toggleProfiler(enable) {
      this.profiler.active = enable;
      this.createProfilingDisplay(enable);
    }

    createProfilingDisplay(visible) {
      if (!this.profilingDisplay) {
        this.profilingDisplay = document.createElement('div');
        this.profilingDisplay.style.position = 'absolute';
        this.profilingDisplay.style.bottom = '10px';
        this.profilingDisplay.style.left = '50%';
        this.profilingDisplay.style.transform = 'translateX(-50%)';
        this.profilingDisplay.style.color = 'white';
        this.profilingDisplay.style.backgroundColor = 'rgba(0,0,0,0.7)';
        this.profilingDisplay.style.padding = '10px';
        this.profilingDisplay.style.fontFamily = 'monospace';
        this.profilingDisplay.style.fontSize = '12px';
        this.profilingDisplay.style.zIndex = '1000';
        this.profilingDisplay.style.maxHeight = '200px';
        this.profilingDisplay.style.overflowY = 'auto';
        
        document.body.appendChild(this.profilingDisplay);
      }
      
      this.profilingDisplay.style.display = visible ? 'block' : 'none';
    }

    updatePerformanceDisplay() {
      if (!this.profilingDisplay || !this.profiler.active) return;
      
      let html = `<strong>Rendering Metrics</strong><br>`;
      html += `FPS: <span style="color:${this.getFPSColor(this.currentFPS)}">${this.currentFPS}</span><br>`;
      
      Object.keys(this.profiler.history).forEach(name => {
        const history = this.profiler.history[name];
        if (history.length > 0) {
          const latest = history[history.length - 1].value;
          html += `${name}: ${latest.toFixed(2)}ms<br>`;
        }
      });
      
      this.profilingDisplay.innerHTML = html;
    }

    getFPSColor(fps) {
      if (fps >= 55) return '#4CAF50'; // Good (green)
      if (fps >= 30) return '#FFC107'; // Warning (yellow)
      return '#F44336'; // Critical (red)
    }

    // Quality preset configurations
    getQualityPresets() {
      return {
        quality: {
          bloom: { enabled: true, strength: 1.25, radius: 0.6, threshold: 0.85 },
          ssao: { enabled: true },
          shadows: { enabled: true, type: THREE.PCFSoftShadowMap },
          antialias: true,
          pixelRatio: window.devicePixelRatio,
          renderDistance: 500000,
          lod: { enabled: true, bias: 1.2 }
        },
        standard: {
          bloom: { enabled: false },
          ssao: { enabled: false },
          shadows: { enabled: true, type: THREE.PCFSoftShadowMap },
          antialias: false,
          pixelRatio: window.devicePixelRatio,
          renderDistance: this.defaultFarPlane,
          lod: { enabled: true, bias: 1.0 }
        },
        performance: {
          bloom: { enabled: false },
          ssao: { enabled: false },
          shadows: { enabled: false },
          antialias: false,
          pixelRatio: 1,
          renderDistance: 15000,
          lod: { enabled: true, bias: 0.6 }
        }
      };
    }
    
    applyQualityPreset(presetName) {
      const presets = this.getQualityPresets();
      const preset = presets[presetName] || presets.standard;
      
      // Set current quality mode globally
      window.currentQualityMode = presetName;
      console.log(`Applying quality preset: ${presetName}`);
      
      this.startProfiling('applyQualityPreset');
      
      let canApplyFullPreset = true;
      
      // Check available effects
      if (!this.availableEffects) {
        this.checkEffectsAvailability();
      }
      
      // Apply renderer settings based on preset
      if (preset.shadows) {
        this.renderer.shadowMap.enabled = preset.shadows.enabled;
        if (preset.shadows.enabled && preset.shadows.type) {
          this.renderer.shadowMap.type = preset.shadows.type;
        }
      }
      
      this.renderer.antialias = preset.antialias || false;
      this.renderer.setPixelRatio(preset.pixelRatio || 1);
      
      // Configure LOD and distance settings
      this.configureLOD(preset.lod?.enabled || false, {
        bias: preset.lod?.bias || 1.0
      });
      
      if (preset.renderDistance) {
        this.setRenderDistance(preset.renderDistance);
      }
      
      
      if (window.objectManager) {
        
        window.objectManager.setPerformanceMode(presetName === 'performance');
        
       
        if (presetName === 'quality') {
          window.objectManager.forceApplyQualityToAllNodes();
        } else if (presetName === 'standard') {
          window.objectManager.applyStandardMaterials();
        } else if (presetName === 'performance') {
          window.objectManager.applyPerformanceMaterials();
        }
      }
      
      // Apply remaining settings
      this.disableAnimations = presetName === 'performance';
      this.disableNiceMeshes = presetName === 'performance';
      this.displayAllLabels(presetName !== 'performance');
      
      if (window.addStarsToScene) {
        window.addStarsToScene(presetName === 'quality', presetName === 'quality');
      }
  
      this.updateEventBusHandler();
      this.endProfiling('applyQualityPreset');
      
      this.loadingIndicator.textContent = this.getQualityModeDescription(presetName, canApplyFullPreset);
    }
    
    getQualityModeDescription(mode, fullPreset = true) {
      switch(mode) {
        case 'quality':
          return fullPreset 
            ? 'Qualitätsmodus: Bloom, SSAO, Umgebungsspiegelung und erweiterte Beleuchtung aktiviert'
            : 'Qualitätsmodus: Einige Effekte nicht verfügbar. Reduzierte Qualität aktiviert.';
        case 'standard':
          return 'Standardmodus: LOD aktiviert, Bloom deaktiviert';
        case 'performance':
          return 'Performance-Modus: LOD und reduzierte Effekte für maximale Leistung';
        default:
          return 'Rendermodus geändert';
      }
    }
}
