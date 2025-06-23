<script lang="ts">
  import Letter from '$lib/Letter.svelte';

  const messages = [
    {
      id: 1,
      sender: 'Anna (Kollegin)',
      preview: 'Betreff: Meeting morgen...',
      content: 'Hallo! Können wir morgen um 10 Uhr das Meeting zu Thema X halten? Bitte gib Bescheid, ob dir der Termin passt. Viele Grüße, Anna.',
      color: 'bg-rose-100',
      shape: 'rounded-full'
    },
    {
      id: 2,
      sender: 'Herr Müller (Kunde)',
      preview: 'Ihre Anfrage vom Dienstag...',
      content: 'Sehr geehrte/r Frau/Herr [Dein Name], bezüglich Ihrer Anfrage vom Dienstag möchte ich mitteilen, dass wir an einer Lösung arbeiten. Mit freundlichen Grüßen, Herr Müller.',
      color: 'bg-blue-100',
      shape: 'rounded-md'
    },
    {
      id: 3,
      sender: 'Lisa (Kollegin)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-green-100',
      shape: 'rounded-lg'
    },
    {
      id: 4,
      sender: 'Jan (Kollege)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-green-100',
      shape: 'rounded-lg'
    },
    {
      id: 5,
      sender: 'Noah (Kollege)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-rose-100',
      shape: 'rounded-md'
    },
    {
      id: 6,
      sender: 'Herbert (Kollegin)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-blue-100',
      shape: 'rounded-full'
    }
    ,
    {
      id: 7,
      sender: 'Canel (Kollege)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-rose-100',
      shape: 'rounded-md'
    }
    ,
    {
      id: 8,
      sender: 'Herbert (Kollegin)',
      preview: 'Kaffee? 😊',
      content: 'Hey! Lust auf einen Kaffee in der Mittagspause? Bin gleich in der Küche. LG, Lisa.',
      color: 'bg-green-100',
      shape: 'rounded-full'
    }
  ];

  let openMessageId: number | null = null;

  function openLetter(id: number) {
    openMessageId = id;
  }

  function closeLetter() {
    openMessageId = null;
  }
</script>

<div class="message-garden">
  {#each messages as message (message.id)}
    <div
      class="letter-wrapper"
      style="
        top: {Math.random() * 75 + 5}vh;
        left: {Math.random() * 75 + 5}vw;
        transform: rotate({(Math.random() * 30) - 15}deg);"
    >
      <Letter
        message={message}
        isOpen={openMessageId === message.id}
        on:open={() => openLetter(message.id)}
        on:close={closeLetter}
      />
    </div>
  {/each}

  {#if openMessageId !== null}
    <div class="overlay" on:click={closeLetter}></div>
  {/if}
</div>

<style>
  .message-garden {
    position: relative;
    width: 100vw;
    min-height: 100vh;
    background: linear-gradient(135deg, #e0f7fa, #fce4ec);
    overflow: hidden;
    font-family: 'Handlee', cursive;
    margin-left: var(--navbar-width);
  }

  @import url('https://fonts.googleapis.com/css2?family=Handlee&display=swap');

  .letter-wrapper {
    position: absolute;
    transition: transform 0.3s ease, top 0.3s ease, left 0.3s ease;
    z-index: 10;
  }

  .letter-wrapper:hover {
    transform: scale(1.05) rotate(calc(var(--initial-rotation) * 1.05));
    z-index: 20;
  }
</style>