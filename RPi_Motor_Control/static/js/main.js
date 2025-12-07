// RPi Motor Control - Main JavaScript

// WebSocket connection
let socket = null;
let selectedLogic = null;
let selectedMode = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  initWebSocket();
  loadInitialStatus();
  startStatusPolling();
});

// Initialize WebSocket connection
function initWebSocket() {
  socket = io();

  socket.on("connect", function () {
    console.log("Connected to server");
    updateConnectionStatus(true);
    showNotification("Connected to server", "success");
  });

  socket.on("disconnect", function () {
    console.log("Disconnected from server");
    updateConnectionStatus(false);
    showNotification("Disconnected from server", "error");
  });

  socket.on("status_update", function (data) {
    updateStatus(data);
  });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
  const statusBadge = document.getElementById("connection-status");
  if (connected) {
    statusBadge.textContent = "Connected";
    statusBadge.classList.remove("disconnected");
    statusBadge.classList.add("connected");
  } else {
    statusBadge.textContent = "Disconnected";
    statusBadge.classList.remove("connected");
    statusBadge.classList.add("disconnected");
  }
}

// Load initial status
function loadInitialStatus() {
  fetch("/api/status")
    .then((response) => response.json())
    .then((data) => updateStatus(data))
    .catch((error) => console.error("Error loading status:", error));
}

// Poll status periodically (backup for WebSocket)
function startStatusPolling() {
  setInterval(() => {
    if (!socket || !socket.connected) {
      loadInitialStatus();
    }
  }, 5000); // Every 5 seconds
}

// Update status display
function updateStatus(data) {
  console.log("Status update:", data);

  // Update selected/active logic
  if (data.selected_logic) {
    selectedLogic =
      data.selected_logic === "logic_a"
        ? "A"
        : data.selected_logic === "logic_b"
        ? "B"
        : null;

    // Update the current logic badge
    updateCurrentLogicDisplay(selectedLogic);
  }

  // Update active logic display in status section (show selected logic, not execution state)
  const activeLogic =
    data.selected_logic === "logic_a"
      ? "Logic A"
      : data.selected_logic === "logic_b"
      ? "Logic B"
      : "None";
  document.getElementById("active-logic").textContent = activeLogic;

  // Update logic status
  const logicStatus = data.logic_a_status || data.logic_b_status;
  if (logicStatus) {
    document.getElementById("current-mode").textContent =
      logicStatus.mode || "-";
    document.getElementById("current-phase").textContent =
      logicStatus.phase || "-";
    document.getElementById("current-position").textContent =
      logicStatus.position || "-";
    document.getElementById("cycle-count").textContent =
      logicStatus.cycle_count || "0";
    document.getElementById("running-status").textContent = logicStatus.running
      ? "Yes"
      : "No";

    // Update manual mode indicator
    const manualModeIndicator = document.getElementById(
      "manual-mode-indicator"
    );
    const manualModeBtn = document.getElementById("manual-mode-btn");
    const autoModeBtn = document.getElementById("auto-mode-btn");

    if (logicStatus.manual_mode) {
      manualModeIndicator.style.display = "block";
      if (manualModeBtn) {
        manualModeBtn.classList.add("btn-active");
        manualModeBtn.disabled = true;
      }
      if (autoModeBtn) {
        autoModeBtn.classList.remove("btn-active");
        autoModeBtn.disabled = false;
      }
    } else {
      manualModeIndicator.style.display = "none";
      if (manualModeBtn) {
        manualModeBtn.classList.remove("btn-active");
        manualModeBtn.disabled = false;
      }
      if (autoModeBtn) {
        autoModeBtn.classList.add("btn-active");
        autoModeBtn.disabled = true;
      }
    }

    if (logicStatus.selected_mode) {
      selectedMode = logicStatus.selected_mode;
      document.getElementById("selected-mode-display").textContent =
        selectedMode;

      // Update mode button states
      document
        .querySelectorAll(".mode-btn, .mode-btn-large")
        .forEach((btn) => btn.classList.remove("selected"));
      const modeButtons = document.querySelectorAll(".mode-btn-large");
      if (modeButtons.length > 0) {
        modeButtons[selectedMode - 1]?.classList.add("selected");
      } else {
        document
          .querySelectorAll(".mode-btn")
          [selectedMode - 1]?.classList.add("selected");
      }
    }
  }

  // Update RTC display for Logic B
  if (data.logic_b_status && data.logic_b_status.rtc_datetime) {
    document.getElementById("rtc-display").textContent =
      data.logic_b_status.rtc_datetime;
  }

  // Update system info tab
  if (document.getElementById("system-info")) {
    document.getElementById("system-info").textContent = JSON.stringify(
      data,
      null,
      2
    );
  }

  // Update RTC info tab
  if (data.rtc_info && document.getElementById("rtc-info")) {
    document.getElementById("rtc-info").textContent = JSON.stringify(
      data.rtc_info,
      null,
      2
    );
  }
}

// Select logic (A or B)
function selectLogic(logic) {
  fetch("/api/select_logic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ logic: logic }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(`Logic ${logic} selected`, "success");
        selectedLogic = logic;
        document.getElementById("selected-logic-display").textContent = logic;

        // Update button states
        document
          .querySelectorAll(".logic-btn")
          .forEach((btn) => btn.classList.remove("selected"));
        document
          .getElementById(`logic-${logic.toLowerCase()}-btn`)
          .classList.add("selected");
        
        // Automatically start the logic thread so it's ready to receive button presses
        fetch("/api/start", { method: "POST" })
          .then((res) => res.json())
          .then((startData) => {
            if (startData.success) {
              console.log("Logic thread started");
            } else {
              // Logic might already be running, that's okay
              console.log("Logic thread status:", startData.error);
            }
          });
      } else {
        showNotification(data.error || "Failed to select logic", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error selecting logic", "error");
    });
}

// Select mode (1-5)
function selectMode(mode) {
  if (!selectedLogic) {
    showNotification("Please select a logic first", "warning");
    return;
  }

  fetch("/api/select_mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: mode }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(`Mode ${mode} selected`, "success");
        selectedMode = mode;
        document.getElementById("selected-mode-display").textContent = mode;

        // Update button states
        document
          .querySelectorAll(".mode-btn")
          .forEach((btn) => btn.classList.remove("selected"));
        document
          .querySelectorAll(".mode-btn")
          [mode - 1].classList.add("selected");
      } else {
        showNotification(data.error || "Failed to select mode", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error selecting mode", "error");
    });
}

// Start execution
function startExecution() {
  if (!selectedLogic) {
    showNotification("Please select a logic first", "warning");
    return;
  }

  if (!selectedMode) {
    showNotification("Please select a mode first", "warning");
    return;
  }

  // The Start button simulates pressing the physical Start button
  // This allows the logic's _handle_waiting_mode() to detect it
  fetch("/api/button/start", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Start button pressed", "success");
      } else {
        showNotification(data.error || "Failed to press start button", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error pressing start button", "error");
    });
}

// Stop execution
function stopExecution() {
  // The Stop button simulates pressing the physical Stop button
  fetch("/api/button/stop", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Stop button pressed", "success");
      } else {
        showNotification(data.error || "Failed to press stop button", "warning");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error pressing stop button", "error");
    });
}

// Emergency stop
function emergencyStop() {
  if (!confirm("⚠️ EMERGENCY STOP - Are you sure?")) {
    return;
  }

  fetch("/api/emergency_stop", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      showNotification("EMERGENCY STOP executed", "warning");
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error executing emergency stop", "error");
    });
}

// Enable manual mode
function enableManual() {
  fetch("/api/manual/enable", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Manual mode enabled", "info");
      } else {
        showNotification(data.error || "Failed to enable manual mode", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error enabling manual mode", "error");
    });
}

// Disable manual mode
function disableManual() {
  fetch("/api/manual/disable", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Manual mode disabled", "info");
      } else {
        showNotification(
          data.error || "Failed to disable manual mode",
          "error"
        );
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error disabling manual mode", "error");
    });
}

// Show notification
function showNotification(message, type = "info") {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.className = `notification ${type}`;
  notification.style.display = "block";

  setTimeout(() => {
    notification.style.display = "none";
  }, 3000);
}

// Tab switching
function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Remove active class from all buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
  });

  // Show selected tab
  document.getElementById(`${tabName}-tab`).classList.add("active");

  // Activate button
  event.target.classList.add("active");
}

// New functions for redesigned UI

// Update current logic display badge
function updateCurrentLogicDisplay(logic) {
  const logicName = document.getElementById("current-logic-name");
  const logicDesc = document.getElementById("current-logic-desc");

  if (!logic) {
    logicName.textContent = "None Selected";
    logicDesc.textContent = "Please select a logic to begin";
    return;
  }

  if (logic === "A") {
    logicName.textContent = "Logic A";
    logicDesc.textContent = "Standard Control Mode";
  } else if (logic === "B") {
    logicName.textContent = "Logic B";
    logicDesc.textContent = "With RTC Date Check";
  }
}

// Show change logic dialog
function showChangeLogicDialog() {
  const modal = document.getElementById("logic-change-modal");
  modal.classList.add("active");

  // Pre-select current logic
  if (selectedLogic === "A") {
    document.getElementById("radio-logic-a").checked = true;
  } else if (selectedLogic === "B") {
    document.getElementById("radio-logic-b").checked = true;
  }

  // Clear password and error
  document.getElementById("logic-password").value = "";
  document.getElementById("logic-error-message").style.display = "none";

  // Focus on password field if logic is already selected
  if (selectedLogic) {
    setTimeout(() => {
      document.getElementById("logic-password").focus();
    }, 100);
  }
}

// Close change logic dialog
function closeChangeLogicDialog() {
  const modal = document.getElementById("logic-change-modal");
  modal.classList.remove("active");
}

// Confirm logic change with password verification
async function confirmLogicChange() {
  const newLogic = document.querySelector(
    'input[name="new-logic"]:checked'
  )?.value;
  const password = document.getElementById("logic-password").value;
  const errorDiv = document.getElementById("logic-error-message");

  // Validation
  if (!newLogic) {
    errorDiv.textContent = "Please select a logic";
    errorDiv.style.display = "block";
    return;
  }

  if (!password) {
    errorDiv.textContent = "Please enter password";
    errorDiv.style.display = "block";
    return;
  }

  try {
    // Verify password using engineer login endpoint
    const authResponse = await fetch("/api/engineer/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: password }),
    });

    const authData = await authResponse.json();

    if (!authData.success) {
      errorDiv.textContent = "Invalid password";
      errorDiv.style.display = "block";
      document.getElementById("logic-password").value = "";
      return;
    }

    // Password verified, now change logic
    const logicResponse = await fetch("/api/select_logic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logic: newLogic }),
    });

    const logicData = await logicResponse.json();

    if (logicData.success) {
      selectedLogic = newLogic;
      updateCurrentLogicDisplay(newLogic);
      closeChangeLogicDialog();
      showNotification(`Logic ${newLogic} selected successfully`, "success");

      // Logout from engineer session
      await fetch("/api/engineer/logout", { method: "POST" });
    } else {
      errorDiv.textContent = logicData.error || "Failed to change logic";
      errorDiv.style.display = "block";
    }
  } catch (error) {
    console.error("Error:", error);
    errorDiv.textContent = "Error changing logic: " + error.message;
    errorDiv.style.display = "block";
  }
}

// Close modal when clicking outside
document.addEventListener("click", function (event) {
  const modal = document.getElementById("logic-change-modal");
  if (event.target === modal) {
    closeChangeLogicDialog();
  }
});

// Handle Enter key in password field
document.addEventListener("DOMContentLoaded", function () {
  const passwordField = document.getElementById("logic-password");
  if (passwordField) {
    passwordField.addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        confirmLogicChange();
      }
    });
  }
});
