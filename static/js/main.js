// main.js
document.addEventListener("DOMContentLoaded", (event) => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const promptTextarea = document.getElementById("prompt");
  const imagePreview = document.getElementById("imagePreview");
  const imageUrlInput = document.getElementById("imageUrl");
  const analyzeButton = document.getElementById("analyzeButton");
  const resultDiv = document.getElementById("result");
  const saveResultsButton = document.getElementById("saveResults");
  const recentAnalysesList = document.getElementById("recentAnalyses");
  const darkModeToggle = document.getElementById("darkModeToggle");
  const resultPromptDiv = document.getElementById("resultPrompt");
  const resultAnswerDiv = document.getElementById("resultAnswer");

  let currentImageSource = "";
  let selectedFile = null;
  let isAnalyzing = false;

  function updateImageSource(source) {
    currentImageSource = source;
  }

  // Dark mode toggle
  darkModeToggle.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark");
    localStorage.setItem(
      "darkMode",
      document.documentElement.classList.contains("dark")
    );
  });

  // Check for saved dark mode preference
  if (localStorage.getItem("darkMode") === "true") {
    document.documentElement.classList.add("dark");
  }

  function updatePreview(src) {
    if (src) {
      imagePreview.src = src;
      imagePreview.classList.remove("hidden");
    } else {
      imagePreview.classList.add("hidden");
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("bg-gray-200", "dark:bg-gray-700");

    let file;
    if (e.dataTransfer.items) {
      for (let i = 0; i < e.dataTransfer.items.length; i++) {
        if (e.dataTransfer.items[i].kind === "file") {
          file = e.dataTransfer.items[i].getAsFile();
          break;
        }
      }
    } else {
      file = e.dataTransfer.files[0];
    }
    if (file && file.type.startsWith("image/")) {
      selectedFile = file;
      dropZone.textContent = `Selected: ${file.name}`;
      updatePreview(URL.createObjectURL(file));
      updateImageSource(`File: ${file.name}`);
    } else if (e.dataTransfer.getData("text/html")) {
      const html = e.dataTransfer.getData("text/html");
      const match = html.match(/<img[^>]+src="?([^"\s]+)"?\s*/);
      if (match) {
        const imgUrl = match[1];
        imageUrlInput.value = imgUrl;
        updatePreview(imgUrl);
        updateImageSource(`URL: ${imgUrl}`);
      }
    }
  }

  // Drag and drop event listeners
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, highlight, false);
    document.body.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, unhighlight, false);
    document.body.addEventListener(eventName, unhighlight, false);
  });

  function highlight(e) {
    dropZone.classList.add("bg-gray-200", "dark:bg-gray-700");
  }

  function unhighlight(e) {
    dropZone.classList.remove("bg-gray-200", "dark:bg-gray-700");
  }

  dropZone.addEventListener("drop", handleDrop, false);
  document.body.addEventListener("drop", handleDrop, false);

  dropZone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    selectedFile = e.target.files[0];
    dropZone.textContent = `Selected: ${selectedFile.name}`;
    updatePreview(URL.createObjectURL(selectedFile));
  });

  imageUrlInput.addEventListener("input", () => {
    if (imageUrlInput.value) {
      updatePreview(imageUrlInput.value);
    }
  });

  promptTextarea.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isAnalyzing) {
        analyze();
      }
    }
  });

  async function analyze() {
    if (isAnalyzing) return;

    isAnalyzing = true;
    analyzeButton.disabled = true;
    resultPromptDiv.textContent = "Analyzing...";
    resultAnswerDiv.textContent = "";

    const formData = new FormData();
    formData.append("prompt", promptTextarea.value);

    if (selectedFile) {
      formData.append("image_source", "file");
      formData.append("image_file", selectedFile);
    } else if (imageUrlInput.value) {
      formData.append("image_source", "url");
      formData.append("image_url", imageUrlInput.value);
    } else {
      resultAnswerDiv.textContent = "Please select an image or provide a URL.";
      isAnalyzing = false;
      analyzeButton.disabled = false;
      return;
    }

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      const reader = response.body.getReader();
      let result = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = new TextDecoder().decode(value);
        result += text;

        // Separate prompt and answer
        const parts = result.split(promptTextarea.value);
        if (parts.length > 1) {
          resultPromptDiv.textContent = promptTextarea.value;
          resultAnswerDiv.textContent = parts[1].replace("<eos>", "").trim();
        } else {
          resultAnswerDiv.textContent = result;
        }

        if (text.includes("<eos>")) {
          break;
        }
      }

      saveRecentAnalysis(result.trim());
    } catch (error) {
      resultAnswerDiv.textContent = "An error occurred: " + error;
    } finally {
      isAnalyzing = false;
      analyzeButton.disabled = false;
    }
  }

  analyzeButton.addEventListener("click", analyze);

  fileInput.addEventListener("change", (e) => {
    selectedFile = e.target.files[0];
    dropZone.textContent = `Selected: ${selectedFile.name}`;
    updatePreview(URL.createObjectURL(selectedFile));
    updateImageSource(`File: ${selectedFile.name}`);
  });

  imageUrlInput.addEventListener("input", () => {
    if (imageUrlInput.value) {
      updatePreview(imageUrlInput.value);
      updateImageSource(`URL: ${imageUrlInput.value}`);
    }
  });

  function formatDateTime(date) {
    // Format date as yyyy-MM-DD
    const dateOptions = { year: "numeric", month: "2-digit", day: "2-digit" };
    const formattedDate = new Intl.DateTimeFormat("en-CA", dateOptions).format(
      date
    );

    // Format time based on locale
    const timeOptions = { hour: "2-digit", minute: "2-digit" };
    const formattedTime = new Intl.DateTimeFormat(
      undefined,
      timeOptions
    ).format(date);

    return `${formattedDate} ${formattedTime}`;
  }

  function saveRecentAnalysis(result) {
    let recentAnalyses = JSON.parse(
      localStorage.getItem("recentAnalyses") || "[]"
    );
    recentAnalyses.unshift({
      prompt: promptTextarea.value,
      result: result,
      imageSource: currentImageSource,
      timestamp: formatDateTime(new Date()),
    });
    recentAnalyses = recentAnalyses.slice(0, 5); // Keep only the 5 most recent analyses
    localStorage.setItem("recentAnalyses", JSON.stringify(recentAnalyses));
    updateRecentAnalysesList();
  }

  function updateRecentAnalysesList() {
    const recentAnalyses = JSON.parse(
      localStorage.getItem("recentAnalyses") || "[]"
    );
    recentAnalysesList.innerHTML = "";
    recentAnalyses.forEach((analysis, index) => {
      const li = document.createElement("li");
      li.className =
        "cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 p-2 rounded transition-colors duration-300";
      li.textContent = `${analysis.timestamp}: ${analysis.prompt.substring(
        0,
        30
      )}...`;
      li.addEventListener("click", () => {
        promptTextarea.value = analysis.prompt;
        resultPromptDiv.textContent = analysis.prompt;
        resultAnswerDiv.textContent = analysis.result;
        currentImageSource = analysis.imageSource;
      });
      recentAnalysesList.appendChild(li);
    });
  }

  saveResultsButton.addEventListener("click", () => {
    const prompt = resultPromptDiv.textContent;
    const answer = resultAnswerDiv.textContent;
    const timestamp = formatDateTime(new Date());

    const resultText = `Analysis Result (${timestamp})
Image Source: ${currentImageSource}
Prompt: ${prompt}

Answer: ${answer}`;

    const blob = new Blob([resultText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analysis_result_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Initialize recent analyses list
  updateRecentAnalysesList();
});
