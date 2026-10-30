import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './contexts/LanguageContext';
import { FarmProvider } from './contexts/FarmContext';
import { ChatProvider } from './contexts/ChatContext';
import { TopHeader } from './components/layout/TopHeader';
import { LocationModal } from './components/modals/LocationModal';
import { LanguageModal } from './components/modals/LanguageModal';
import { NotificationsDrawer } from './components/modals/NotificationsDrawer';
import { HelpCenterModal } from './components/modals/HelpCenterModal';

import { Home } from './pages/Home';
import { Chat } from './pages/Chat';
import { Recommend } from './pages/Recommend';
import { Soil } from './pages/Soil';
import { Weather } from './pages/Weather';
import { Crops } from './pages/Crops';
import { CropDetail } from './pages/CropDetail';
import { Farm } from './pages/Farm';
import { Market } from './pages/Market';
import { Admin } from './pages/Admin';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  return (
    <BrowserRouter>
      <LanguageProvider>
        <FarmProvider>
          <ChatProvider>
            <div className="min-h-screen bg-[#F8FAF9] text-[#0F281E] flex flex-col font-sans selection:bg-[#00A859]/20 selection:text-[#007A40]">
              
              {/* Top Navigation Header */}
              <TopHeader
                onOpenLocation={() => setIsLocationOpen(true)}
                onOpenLanguage={() => setIsLanguageOpen(true)}
                onOpenNotifications={() => setIsNotificationsOpen(true)}
              />

              {/* Main Content Viewport */}
              <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/recommend" element={<Recommend />} />
                  <Route path="/market" element={<Market />} />
                  <Route path="/soil" element={<Soil />} />
                  <Route path="/weather" element={<Weather />} />
                  <Route path="/crops" element={<Crops />} />
                  <Route path="/crops/:id" element={<CropDetail />} />
                  <Route path="/farm" element={<Navigate to="/" replace />} />
                  <Route path="/admin" element={<Admin />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </main>

              {/* Global Modals & Drawers */}
              <LocationModal
                isOpen={isLocationOpen}
                onClose={() => setIsLocationOpen(false)}
              />

              <LanguageModal
                isOpen={isLanguageOpen}
                onClose={() => setIsLanguageOpen(false)}
              />

              <NotificationsDrawer
                isOpen={isNotificationsOpen}
                onClose={() => setIsNotificationsOpen(false)}
              />

              <HelpCenterModal
                isOpen={isHelpOpen}
                onClose={() => setIsHelpOpen(false)}
              />

            </div>
          </ChatProvider>
        </FarmProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
};

export default App;
