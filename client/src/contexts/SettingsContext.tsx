import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type ScreenshotMode = "every-step" | "last-step" | "none";

interface SettingsContextType {
  model: string;
  setModel: (model: string) => void;
  screenshotMode: ScreenshotMode;
  setScreenshotMode: (mode: ScreenshotMode) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

const DEFAULT_MODEL = "google/gemini-2.5-flash";
const DEFAULT_SCREENSHOT_MODE: ScreenshotMode = "last-step";

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [model, setModelState] = useState<string>(DEFAULT_MODEL);
  const [screenshotMode, setScreenshotModeState] = useState<ScreenshotMode>(DEFAULT_SCREENSHOT_MODE);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedModel = localStorage.getItem("stagehand-model");
      if (savedModel) {
        setModelState(savedModel);
      }
      
      const savedScreenshotMode = localStorage.getItem("stagehand-screenshot-mode") as ScreenshotMode;
      if (savedScreenshotMode && ["every-step", "last-step", "none"].includes(savedScreenshotMode)) {
        setScreenshotModeState(savedScreenshotMode);
      }
      
      setIsInitialized(true);
    }
  }, []);

  useEffect(() => {
    if (isInitialized && typeof window !== "undefined") {
      localStorage.setItem("stagehand-model", model);
    }
  }, [model, isInitialized]);

  useEffect(() => {
    if (isInitialized && typeof window !== "undefined") {
      localStorage.setItem("stagehand-screenshot-mode", screenshotMode);
    }
  }, [screenshotMode, isInitialized]);

  const setModel = (newModel: string) => {
    setModelState(newModel);
  };

  const setScreenshotMode = (mode: ScreenshotMode) => {
    setScreenshotModeState(mode);
  };

  return (
    <SettingsContext.Provider value={{ model, setModel, screenshotMode, setScreenshotMode }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
