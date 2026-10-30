import React from 'react';
import { X, Bell, CloudRain, TrendingUp, FlaskConical, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { useFarm } from '../../contexts/FarmContext';

interface NotificationsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationsDrawer: React.FC<NotificationsDrawerProps> = ({ isOpen, onClose }) => {
  const { farm } = useFarm();
  if (!isOpen) return null;

  const alerts = [
    {
      id: 'n1',
      title: `Rainfall Advisory for ${farm.district}`,
      description: 'Light to moderate Kharif showers (12mm) anticipated in the next 48 hours. Regulate drip fertigation.',
      time: '20 mins ago',
      type: 'weather',
      unread: true
    },
    {
      id: 'n2',
      title: 'APMC Market Benchmark Update',
      description: `${farm.district} APMC benchmark price updated to ₹7,450/quintal (up 3.2% this week).`,
      time: '2 hours ago',
      type: 'market',
      unread: true
    },
    {
      id: 'n3',
      title: 'Soil Nutrient Testing Season',
      description: 'Pre-sowing soil health card update recommended for Kharif season micro-nutrients (Zinc & Boron).',
      time: '1 day ago',
      type: 'soil',
      unread: false
    },
    {
      id: 'n4',
      title: 'PMFBY Kharif Enrollment Active',
      description: 'Pradhan Mantri Fasal Bima Yojana cut-off date is approaching. Protect your Cotton and Pulses.',
      time: '3 days ago',
      type: 'scheme',
      unread: false
    }
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case 'weather': return <CloudRain className="w-4 h-4 text-[#55A9E8]" />;
      case 'market': return <TrendingUp className="w-4 h-4 text-[#08A873]" />;
      case 'soil': return <FlaskConical className="w-4 h-4 text-[#F4B740]" />;
      default: return <ShieldAlert className="w-4 h-4 text-[#EF6B73]" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md h-full bg-[#111E31] border-l border-[#26374D] shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#26374D] bg-[#17263A]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#08A873]/15 text-[#08A873] border border-[#08A873]/30">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#F5F8FC]">Agricultural Alerts</h3>
              <p className="text-xs text-[#A9B7C8]">2 unread notifications for {farm.district}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-[#A9B7C8] hover:text-white hover:bg-[#26374D] transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#0C1728]">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border transition ${
                alert.unread
                  ? 'bg-[#17263A] border-[#08A873]/60 shadow-sm'
                  : 'bg-[#111E31] border-[#26374D] opacity-80'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[#0C1728] border border-[#26374D] shrink-0 mt-0.5">
                  {getIcon(alert.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-semibold text-sm text-[#F5F8FC]">{alert.title}</h4>
                    {alert.unread && (
                      <span className="w-2 h-2 rounded-full bg-[#08A873] shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-[#A9B7C8] mt-1 leading-relaxed">{alert.description}</p>
                  <span className="text-[11px] text-[#718197] mt-2 block">{alert.time}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#26374D] bg-[#17263A] flex items-center justify-between">
          <button className="text-xs font-semibold text-[#08A873] hover:underline flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Mark all as read</span>
          </button>
          <button onClick={onClose} className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#26374D] text-[#F5F8FC] hover:bg-[#3B5270]">
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
