document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const resultsContainer = document.getElementById("search-results");
  const btn = document.getElementById('profile-menu-button');
  const dropdown = document.getElementById('profile-dropdown');

  searchInput.addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    if (query.length < 2) {
      resultsContainer.classList.add("hidden");
      return;
    }

    try {
      const response = await fetch(
        `/panel/products/search-suggestions?q=${encodeURIComponent(query)}`,
      );
      const suggestions = await response.json();

      if (suggestions.length > 0) {
        resultsContainer.innerHTML = suggestions
          .map(
            (item) => `
            <a href="${item.url}" class="flex items-center justify-between px-5 py-3 hover:bg-slate-50 transition-colors group">
                <div class="flex flex-col">
                    <span class="text-sm font-bold text-[#243c60] group-hover:text-[#7dc6e9]">${item.nombre}</span>
                    <span class="text-[10px] uppercase tracking-widest text-slate-400 font-black">${item.tipo}</span>
                </div>
                <svg class="w-4 h-4 text-slate-300 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M9 5l7 7-7 7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </a>
        `,
          )
          .join("");
        resultsContainer.classList.remove("hidden");
      } else {
        resultsContainer.classList.add("hidden");
      }
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    }
  });

  // Cerrar resultados al hacer click fuera
  document.addEventListener("click", (e) => {
    if (
      !searchInput.contains(e.target) &&
      !resultsContainer.contains(e.target)
    ) {
      resultsContainer.classList.add("hidden");
    }
  });
  btn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('invisible');
        dropdown.classList.toggle('opacity-0');
        dropdown.classList.toggle('translate-y-2');
    });

    // Cerrar si se hace click fuera
    document.addEventListener('click', () => {
        dropdown.classList.add('invisible');
        dropdown.classList.add('opacity-0');
        dropdown.classList.add('translate-y-2');
    });
});
