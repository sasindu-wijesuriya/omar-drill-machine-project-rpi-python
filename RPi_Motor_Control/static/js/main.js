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
    document.getElementById("selected-logic-display").textContent =
      selectedLogic || "None";

    // Update button states
    document
      .querySelectorAll(".logic-btn")
      .forEach((btn) => btn.classList.remove("selected"));
    if (selectedLogic) {
      document
        .getElementById(`logic-${selectedLogic.toLowerCase()}-btn`)
        .classList.add("selected");
    }
  }

  // Update active logic display
  const activeLogic =
    data.active_logic === "logic_a"
      ? "A"
      : data.active_logic === "logic_b"
      ? "B"
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

    if (logicStatus.selected_mode) {
      selectedMode = logicStatus.selected_mode;
      document.getElementById("selected-mode-display").textContent =
        selectedMode;

      // Update mode button states
      document
        .querySelectorAll(".mode-btn")
        .forEach((btn) => btn.classList.remove("selected"));
      document
        .querySelectorAll(".mode-btn")
        [selectedMode - 1]?.classList.add("selected");
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

  if (!confirm("Start execution?")) {
    return;
  }

  fetch("/api/start", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Execution started", "success");
      } else {
        showNotification(data.error || "Failed to start", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error starting execution", "error");
    });
}

// Stop execution
function stopExecution() {
  if (!confirm("Stop execution?")) {
    return;
  }

  fetch("/api/stop", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Execution stopped", "success");
      } else {
        showNotification(data.error || "Failed to stop", "warning");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Error stopping execution", "error");
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
