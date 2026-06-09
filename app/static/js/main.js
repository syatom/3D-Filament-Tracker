// Custom JavaScript for Spool Tracker

// ========================================
// DARK MODE FUNCTIONALITY
// ========================================

/**
 * Update dark mode icon and text based on current state
 * @param {boolean} isDarkMode - Current dark mode state
 */
function updateDarkModeIcon(isDarkMode) {
  const icon = document.getElementById("darkModeIcon");
  const text = document.getElementById("darkModeText");

  if (icon && text) {
    if (isDarkMode) {
      icon.className = "bi bi-sun-fill";
      text.textContent = "Light Mode";
    } else {
      icon.className = "bi bi-moon-fill";
      text.textContent = "Dark Mode";
    }
  }
}

/**
 * Toggle dark mode theme
 */
function toggleDarkMode() {
  const htmlElement = document.documentElement;
  const currentTheme = htmlElement.getAttribute("data-bs-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  const isDarkMode = newTheme === "dark";

  // Apply theme immediately for instant feedback
  htmlElement.setAttribute("data-bs-theme", newTheme);
  updateDarkModeIcon(isDarkMode);

  // Save preference to server
  fetch("/auth/toggle-dark-mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        console.error("Server error:", response.status, response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data.success) {
        console.error("Failed to save dark mode preference:", data.error);
        // Revert the change
        htmlElement.setAttribute("data-bs-theme", currentTheme);
        updateDarkModeIcon(currentTheme === "dark");
      }
    })
    .catch((error) => {
      console.error("Error toggling dark mode:", error);
      // Revert the visual change if save fails
      htmlElement.setAttribute("data-bs-theme", currentTheme);
      updateDarkModeIcon(currentTheme === "dark");
    });
}

/**
 * Get CSRF token from meta tag or cookie
 * @returns {string} CSRF token
 */
function getCsrfToken() {
  // Try to get from meta tag first
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  if (metaToken) {
    return metaToken.getAttribute("content");
  }

  // Fallback to cookie
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "csrf_token") {
      return decodeURIComponent(value);
    }
  }

  return "";
}

// Initialize dark mode toggle on page load
document.addEventListener("DOMContentLoaded", function () {
  const darkModeToggle = document.getElementById("darkModeToggle");

  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", function (e) {
      e.preventDefault();
      toggleDarkMode();
    });
  }
});
