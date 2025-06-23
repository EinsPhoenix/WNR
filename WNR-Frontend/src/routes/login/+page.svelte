<script lang="ts">
  import { goto } from "$app/navigation";

  function login() {
    localStorage.setItem('loggedIn', 'true');
    goto('/');
  }
</script>

<div class="login-wrapper">
  <div class="login-container">
    <h1>Welcome Back!</h1>
    <button on:click={login}>Join In 💖</button>
  </div>
</div>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

  html, body {
    height: 100%;
    margin: 0;
    background: linear-gradient(135deg, #fceaff, #ffd1f9);
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: 'Poppins', sans-serif;
    overflow: hidden;
  }

  .login-wrapper {
    perspective: 1000px;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100vw;
    height: 100vh;
  }

  .login-container {
    background: linear-gradient(145deg, #ffb3de, #ff84cb);
    border-radius: 24px;
    box-shadow:
      0 20px 40px rgba(255, 30, 117, 0.4),
      inset 0 -4px 12px rgba(255, 255, 255, 0.3);
    padding: 4rem 3rem;
    width: 380px;
    text-align: center;
    color: #fff;
    transform-style: preserve-3d;
    animation: float 6s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0) rotateX(0deg) rotateY(0deg); }
    50% { transform: translateY(-15px) rotateX(3deg) rotateY(7deg); }
  }

  h1 {
    font-weight: 700;
    font-size: 2.8rem;
    margin-bottom: 2.5rem;
    text-shadow:
      0 3px 10px rgba(255, 255, 255, 0.7),
      0 0 30px rgba(255, 30, 117, 0.8);
  }

  button {
    cursor: pointer;
    font-size: 1.4rem;
    font-weight: 700;
    color: #ff1e75;
    background:
      linear-gradient(145deg, #fff 0%, #ffd4eb 100%);
    border: none;
    border-radius: 20px;
    padding: 1.25rem 0;
    width: 100%;
    box-shadow:
      0 8px 15px rgba(255, 30, 117, 0.4),
      inset 0 -2px 10px rgba(255, 255, 255, 0.9);
    transition:
      background 0.3s ease,
      color 0.3s ease,
      box-shadow 0.3s ease,
      transform 0.3s ease;
    transform-style: preserve-3d;
  }

  button:hover {
    background: linear-gradient(145deg, #ff1e75 0%, #d9005f 100%);
    color: #fff;
    box-shadow:
      0 15px 25px rgba(255, 30, 117, 0.8),
      inset 0 -3px 15px rgba(255, 255, 255, 0.6);
    transform: translateZ(8px) scale(1.05);
  }

  button:active {
    transform: translateZ(3px) scale(0.98);
    box-shadow:
      0 8px 12px rgba(255, 30, 117, 0.6),
      inset 0 -2px 8px rgba(255, 255, 255, 0.9);
  }

  /* Responsive */
  @media (max-width: 420px) {
    .login-container {
      width: 90vw;
      padding: 3rem 2rem;
    }

    h1 {
      font-size: 2rem;
      margin-bottom: 2rem;
    }

    button {
      font-size: 1.2rem;
      padding: 1rem 0;
    }
  }
</style>
