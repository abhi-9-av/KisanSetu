import React, { useEffect, useMemo, useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

type TokenStatus =
  | 'BOOKED'
  | 'ARRIVED'
  | 'WAITING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'CANCELLED';

type PaymentStatus =
  | 'NOT_STARTED'
  | 'PROCUREMENT_COMPLETED'
  | 'PAYMENT_INITIATED'
  | 'PROCESSING'
  | 'PAID';

type AcceptedStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
type Page = 'home' | 'slots' | 'status';

interface Slot {
  date: string;
  start_time: string;
  end_time: string;
}

interface Token {
  token_number: string;
  issued_at: string;
  status: TokenStatus;
}

interface QueueInfo {
  vehicles_ahead: number;
  estimated_wait_min: number;
  last_updated: string;
}

interface Procurement {
  weighment_kg: number | null;
  accepted_status: AcceptedStatus;
  completed_at: string | null;
}

interface Payment {
  status: PaymentStatus;
  amount_inr: number | null;
  initiated_at: string | null;
  paid_at: string | null;
  days_stalled: number;
}

interface BookingData {
  booking_id: string;
  farmer_id: string;
  farmer_name: string;
  phone: string;
  centre_id: string;
  centre_name: string;
  crop_type: string;
  quantity_quintals: number;
  slot: Slot;
  token: Token;
  queue_info: QueueInfo;
  procurement: Procurement;
  payment: Payment;
}

const colors = {
  green: '#1f8a3e',
  greenDark: '#166b30',
  greenLight: '#e6f5ea',
  orange: '#e08a2c',
  background: '#f4f5f4',
  text: '#1c1f1d',
  muted: '#6b746e',
  border: '#eceeec',
};

const initialBooking: BookingData = {
  booking_id: 'BKG-1001',
  farmer_id: 'F-502',
  farmer_name: 'Ramesh Kumar',
  phone: '9876543210',
  centre_id: 'C-07',
  centre_name: 'Krishi Upaj Mandi, Indore',
  crop_type: 'Soybean',
  quantity_quintals: 2,
  slot: {
    date: '2026-05-22',
    start_time: '10:30',
    end_time: '11:00',
  },
  token: {
    token_number: 'A-125',
    issued_at: '2026-05-22T08:02:00+05:30',
    status: 'WAITING',
  },
  queue_info: {
    vehicles_ahead: 24,
    estimated_wait_min: 75,
    last_updated: '2026-05-22T09:30:00+05:30',
  },
  procurement: {
    weighment_kg: 200,
    accepted_status: 'APPROVED',
    completed_at: '2026-05-22T10:45:00+05:30',
  },
  payment: {
    status: 'PROCESSING',
    amount_inr: 5680,
    initiated_at: '2026-05-22T10:45:00+05:30',
    paid_at: null,
    days_stalled: 0,
  },
};

const formatDate = (date: string): string =>
  new Date(`${date}T00:00:00`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

const formatTime = (time: string): string => {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours >= 12 ? 'PM' : 'AM';
  const hour = hours % 12 || 12;
  return `${hour}:${String(minutes).padStart(2, '0')} ${period}`;
};

const formatWait = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return hours > 0
    ? `${hours}h ${remainingMinutes}m`
    : `${remainingMinutes}m`;
};

export default function FarmerDashboard() {
  const [booking, setBooking] = useState<BookingData>(initialBooking);
  const [activePage, setActivePage] = useState<Page>('home');
  const [selectedDate, setSelectedDate] = useState(initialBooking.slot.date);
  const [selectedSlot, setSelectedSlot] = useState(
    `${initialBooking.slot.start_time}-${initialBooking.slot.end_time}`,
  );
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setBooking((current) => {
        if (current.queue_info.vehicles_ahead === 0) {
          return current;
        }

        return {
          ...current,
          token: {
            ...current.token,
            token_number: `A-${Number(current.token.token_number.slice(2)) + 1}`,
          },
          queue_info: {
            ...current.queue_info,
            vehicles_ahead: current.queue_info.vehicles_ahead - 1,
            estimated_wait_min: Math.max(
              5,
              current.queue_info.estimated_wait_min - 3,
            ),
            last_updated: new Date().toISOString(),
          },
        };
      });
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeout = setTimeout(() => setToast(null), 1800);
    return () => clearTimeout(timeout);
  }, [toast]);

  const progress = useMemo(
    () =>
      Math.min(
        95,
        38 + (initialBooking.queue_info.vehicles_ahead - booking.queue_info.vehicles_ahead) * 2.5,
      ),
    [booking.queue_info.vehicles_ahead],
  );

  const showToast = (message: string) => setToast(message);

  const confirmSlot = () => {
    const [startTime, endTime] = selectedSlot.split('-');
    setBooking((current) => ({
      ...current,
      slot: {
        date: selectedDate,
        start_time: startTime,
        end_time: endTime,
      },
      token: {
        ...current.token,
        status: 'BOOKED',
      },
    }));
    showToast(`Slot confirmed! Token ${booking.token.token_number} issued`);
    setActivePage('home');
  };

  return (
    <SafeAreaView className="flex-1 bg-[#0d0f0e]">
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
      <View className="mx-auto my-0 w-full max-w-[390px] flex-1 overflow-hidden rounded-[42px] bg-[#f4f5f4]">
        <ScrollView
          className="flex-1"
          contentContainerStyle={{ paddingBottom: 106 }}
          showsVerticalScrollIndicator={false}
        >
          <View className="px-5 pt-3">
            {activePage === 'home' && (
              <HomePage
                booking={booking}
                progress={progress}
                onAction={showToast}
                onNavigate={setActivePage}
              />
            )}
            {activePage === 'slots' && (
              <SlotsPage
                booking={booking}
                selectedDate={selectedDate}
                selectedSlot={selectedSlot}
                onDateChange={setSelectedDate}
                onSlotChange={setSelectedSlot}
                onConfirm={confirmSlot}
              />
            )}
            {activePage === 'status' && <StatusPage booking={booking} />}
          </View>
        </ScrollView>

        {toast && (
          <View className="absolute bottom-[102px] left-5 right-5 rounded-[14px] bg-[#1c1f1d] px-[18px] py-[13px]">
            <Text className="text-center text-[13px] font-bold text-white">
              {toast}
            </Text>
          </View>
        )}

        <BottomNavigation activePage={activePage} onNavigate={setActivePage} />
      </View>
    </SafeAreaView>
  );
}

function Header({ title = 'KisanSetu' }: { title?: string }) {
  return (
    <View className="mb-[18px] mt-2 flex-row items-center justify-between">
      <Text className="text-[26px] font-bold tracking-[-0.5px] text-[#1f8a3e]">
        {title}
      </Text>
      <TouchableOpacity className="relative h-[38px] w-[38px] items-center justify-center">
        <Text className="text-[22px] text-[#1c1f1d]">♧</Text>
        <View className="absolute right-[6px] top-[6px] h-2 w-2 rounded-full border-2 border-[#f4f5f4] bg-[#e08a2c]" />
      </TouchableOpacity>
    </View>
  );
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <View className={`mb-4 rounded-[20px] border border-[#eceeec] bg-white p-5 shadow-sm ${className}`}>
      {children}
    </View>
  );
}

function HomePage({
  booking,
  progress,
  onAction,
  onNavigate,
}: {
  booking: BookingData;
  progress: number;
  onAction: (message: string) => void;
  onNavigate: (page: Page) => void;
}) {
  const isCalm = booking.queue_info.vehicles_ahead < 10;

  return (
    <>
      <Header />
      <View className="mb-5 flex-row items-center justify-between">
        <View>
          <Text className="mb-1 text-[21px] font-bold text-[#1c1f1d]">
            Namaste, {booking.farmer_name.split(' ')[0]} 👋
          </Text>
          <Text className="text-sm text-[#6b746e]">Aaj ka din shubh ho!</Text>
        </View>
        <View className="h-14 w-14 items-center justify-center rounded-full bg-[#e6f5ea]">
          <Text className="text-[26px]">🧑🏽‍🌾</Text>
        </View>
      </View>

      <Card>
        <Text className="mb-[14px] text-base font-bold text-[#1c1f1d]">
          Your Next Mandi Slot
        </Text>
        <View className="flex-row items-start justify-between gap-3">
          <View className="flex-1 gap-[10px]">
            <Text className="text-[14.5px] text-[#1c1f1d]">📅 {formatDate(booking.slot.date)}</Text>
            <Text className="text-[14.5px] text-[#1c1f1d]">
              🕒 {formatTime(booking.slot.start_time)} – {formatTime(booking.slot.end_time)}
            </Text>
            <Text className="text-[14.5px] text-[#1c1f1d]">📍 {booking.centre_name}</Text>
          </View>
          <View className="min-w-[100px] rounded-[14px] bg-[#e6f5ea] px-4 py-3">
            <Text className="text-center text-[11px] uppercase tracking-[0.5px] text-[#6b746e]">
              ETA
            </Text>
            <Text className="my-0.5 text-center text-[19px] font-bold text-[#166b30]">
              {formatWait(booking.queue_info.estimated_wait_min)}
            </Text>
            <Text className="text-center text-[10.5px] text-[#6b746e]">Updated just now</Text>
          </View>
        </View>
      </Card>

      <Card>
        <Text className="mb-[14px] text-base font-bold text-[#1c1f1d]">Live Queue Status</Text>
        <View className="mb-[14px] flex-row justify-between">
          <View>
            <Text className="mb-0.5 text-[13px] text-[#6b746e]">Your Token</Text>
            <Text className="text-[28px] font-extrabold text-[#1f8a3e]">{booking.token.token_number}</Text>
          </View>
          <View>
            <Text className="mb-0.5 text-right text-[13px] text-[#6b746e]">Ahead of You</Text>
            <Text className="text-right text-[28px] font-extrabold text-[#1c1f1d]">
              {booking.queue_info.vehicles_ahead}
            </Text>
          </View>
        </View>
        <View className="mb-[10px] h-2 overflow-hidden rounded-md bg-[#eceeec]">
          <View className="h-full rounded-md bg-[#1f8a3e]" style={{ width: `${progress}%` }} />
        </View>
        <View className="flex-row justify-between">
          <Text className={`text-[12.5px] font-semibold ${isCalm ? 'text-[#1f8a3e]' : 'text-[#e08a2c]'}`}>
            {isCalm ? 'Mandi Calm' : 'Mandi Crowded'}
          </Text>
          <Text className="text-[12.5px] text-[#6b746e]">
            Average Waiting: {formatWait(booking.queue_info.estimated_wait_min)}
          </Text>
        </View>
      </Card>

      <Card>
        <View className="mb-4 flex-row items-center justify-between">
          <Text className="text-[15px] font-bold text-[#1c1f1d]">Track Your Procurement</Text>
          <Text className="rounded-full bg-[#e6f5ea] px-3 py-[5px] text-[11.5px] font-bold text-[#166b30]">
            {booking.payment.status === 'PAID' ? 'Completed' : 'In Progress'}
          </Text>
        </View>
        <Text className="mb-[14px] text-[14.5px] font-semibold">
          {booking.crop_type} ({booking.quantity_quintals} Quintal)
        </Text>
        <ProcurementSteps booking={booking} />
      </Card>

      <View className="mb-4 flex-row gap-[10px]">
        <ActionButton icon="▣" label="Book Slot" onPress={() => onNavigate('slots')} />
        <ActionButton icon="▢" label="Raise Complaint" onPress={() => onAction('Opening Complaint Form…')} />
        <ActionButton icon="▤" label="My Receipts" onPress={() => onAction('Loading My Receipts…')} />
        <ActionButton icon="♧" label="Notifications" onPress={() => onAction('No new notifications')} />
      </View>
    </>
  );
}

function ProcurementSteps({ booking }: { booking: BookingData }) {
  const completed = booking.procurement.accepted_status === 'APPROVED';
  const paymentDone = booking.payment.status === 'PAID';
  const steps = [
    { title: 'Check-in', sub: '10:15 AM', done: true, icon: '✓' },
    { title: 'Weight Verification', sub: completed ? '10:45 AM' : 'Pending', done: completed, icon: completed ? '✓' : '2' },
    { title: 'Payment', sub: paymentDone ? 'Paid' : 'Pending', done: paymentDone, icon: paymentDone ? '✓' : '◷' },
    { title: 'Receipt', sub: paymentDone ? 'Ready' : 'Pending', done: paymentDone, icon: paymentDone ? '✓' : '▤' },
  ];

  return (
    <View className="relative flex-row justify-between">
      <View className="absolute left-[12.5%] right-[12.5%] top-[17px] h-[3px] bg-[#e2e5e2]">
        <View className="h-full w-1/3 bg-[#1f8a3e]" />
      </View>
      {steps.map((step) => (
        <View className="z-10 flex-1 items-center" key={step.title}>
          <View className={`mb-2 h-[34px] w-[34px] items-center justify-center rounded-full border-[3px] border-[#f4f5f4] ${step.done ? 'bg-[#1f8a3e]' : 'bg-[#e2e5e2]'}`}>
            <Text className={`text-[15px] font-bold ${step.done ? 'text-white' : 'text-[#9aa39c]'}`}>{step.icon}</Text>
          </View>
          <Text className="text-center text-[12.5px] font-semibold text-[#1c1f1d]">{step.title}</Text>
          <Text className="mt-0.5 text-center text-[11px] text-[#6b746e]">{step.sub}</Text>
        </View>
      ))}
    </View>
  );
}

function ActionButton({
  icon,
  label,
  onPress,
}: {
  icon: string;
  label: string;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      className="flex-1 items-center gap-2 rounded-2xl border border-[#eceeec] bg-white px-1 py-[14px]"
      onPress={onPress}
      activeOpacity={0.8}
    >
      <Text className="text-[22px] text-[#1f8a3e]">{icon}</Text>
      <Text className="text-center text-[11.5px] font-semibold text-[#1c1f1d]">{label}</Text>
    </TouchableOpacity>
  );
}

function SlotsPage({
  booking,
  selectedDate,
  selectedSlot,
  onDateChange,
  onSlotChange,
  onConfirm,
}: {
  booking: BookingData;
  selectedDate: string;
  selectedSlot: string;
  onDateChange: (date: string) => void;
  onSlotChange: (slot: string) => void;
  onConfirm: () => void;
}) {
  const dates = [
    { label: 'Thu', date: '2026-05-21', number: '21' },
    { label: 'Fri', date: '2026-05-22', number: '22' },
    { label: 'Sat', date: '2026-05-23', number: '23' },
    { label: 'Sun', date: '2026-05-24', number: '24' },
    { label: 'Mon', date: '2026-05-25', number: '25' },
  ];
  const slots = [
    { value: '08:00-08:30', label: '8:00 – 8:30', remaining: 'Full', full: true },
    { value: '09:00-09:30', label: '9:00 – 9:30', remaining: '12 left', full: false },
    { value: '09:30-10:00', label: '9:30 – 10:00', remaining: 'Full', full: true },
    { value: '10:30-11:00', label: '10:30 – 11:00', remaining: '6 left', full: false },
    { value: '11:30-12:00', label: '11:30 – 12:00', remaining: '18 left', full: false },
    { value: '13:00-13:30', label: '1:00 – 1:30', remaining: '21 left', full: false },
  ];

  return (
    <>
      <Header title="Book a Slot" />
      <Text className="mb-4 mt-[-8px] text-[13.5px] text-[#6b746e]">{booking.centre_name}</Text>
      <Card className="p-4">
        <Text className="mb-[10px] text-base font-bold">Select Date</Text>
        <View className="flex-row gap-2">
          {dates.map((day) => {
            const active = day.date === selectedDate;
            return (
              <TouchableOpacity
                className={`flex-1 items-center gap-1 rounded-[14px] border-[1.5px] px-1 py-[10px] ${active ? 'border-[#1f8a3e] bg-[#1f8a3e]' : 'border-[#eceeec] bg-[#f4f5f4]'}`}
                key={day.date}
                onPress={() => onDateChange(day.date)}
              >
                <Text className={`text-[11px] font-semibold ${active ? 'text-white' : 'text-[#6b746e]'}`}>{day.label}</Text>
                <Text className={`text-base font-bold ${active ? 'text-white' : 'text-[#1c1f1d]'}`}>{day.number}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </Card>
      <Card className="p-4">
        <Text className="mb-[10px] text-base font-bold">Available Time Slots</Text>
        <View className="flex-row flex-wrap gap-[10px]">
          {slots.map((slot) => {
            const selected = slot.value === selectedSlot;
            return (
              <TouchableOpacity
                className={`w-[47%] rounded-xl border-[1.5px] px-3 py-[10px] ${slot.full ? 'border-[#eceeec] bg-[#f3f3f2]' : selected ? 'border-[#1f8a3e] bg-[#1f8a3e]' : 'border-[#eceeec] bg-white'}`}
                disabled={slot.full}
                key={slot.value}
                onPress={() => onSlotChange(slot.value)}
              >
                <Text className={`text-[13px] font-semibold ${slot.full ? 'text-[#b8bdb9]' : selected ? 'text-white' : 'text-[#1c1f1d]'}`}>{slot.label}</Text>
                <Text className={`mt-[3px] text-[11px] ${slot.full ? 'text-[#c3c7c4]' : selected ? 'text-[#e6f5ea]' : 'text-[#6b746e]'}`}>{slot.remaining}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </Card>
      <Card className="p-4">
        <Text className="mb-[10px] text-base font-bold">Crop Details</Text>
        <View className="mb-[10px] flex-row justify-between">
          <Text className="text-sm text-[#6b746e]">Crop</Text>
          <Text className="text-sm font-semibold">{booking.crop_type}</Text>
        </View>
        <View className="flex-row justify-between">
          <Text className="text-sm text-[#6b746e]">Quantity</Text>
          <Text className="text-sm font-semibold">{booking.quantity_quintals} Quintal</Text>
        </View>
      </Card>
      <TouchableOpacity className="mb-4 w-full rounded-2xl bg-[#1f8a3e] px-4 py-4" onPress={onConfirm} activeOpacity={0.85}>
        <Text className="text-center text-[15px] font-bold text-white">Confirm Slot Booking</Text>
      </TouchableOpacity>
    </>
  );
}

function StatusPage({ booking }: { booking: BookingData }) {
  const milestones = [
    ['Slot Booked', `${formatDate(booking.slot.date)} · ${formatTime(booking.slot.start_time)}`, true],
    ['Entered Mandi Gate', 'Check-in confirmed · 10:15 AM', true],
    ['Weight Verified', `${booking.quantity_quintals} Quintal ${booking.crop_type} · 10:45 AM`, booking.procurement.accepted_status === 'APPROVED'],
    ['Payment Processing', 'Awaiting bank confirmation', booking.payment.status === 'PROCESSING'],
    ['Receipt Generation', booking.payment.status === 'PAID' ? 'Ready' : 'Pending', booking.payment.status === 'PAID'],
  ] as const;

  return (
    <>
      <Header title="Status" />
      <Text className="mb-4 mt-[-8px] text-[13.5px] text-[#6b746e]">Live updates on your visit</Text>
      <Card>
        <View className="mb-4 flex-row items-center justify-between">
          <Text className="text-[15px] font-bold">Today&apos;s Visit</Text>
          <Text className="rounded-full bg-[#e6f5ea] px-3 py-[5px] text-[11.5px] font-bold text-[#166b30]">{booking.token.token_number}</Text>
        </View>
        <View className="pl-1">
          {milestones.map(([title, subtitle, done], index) => (
            <View className="flex-row gap-[14px]" key={title}>
              <View className="items-center">
                <View className={`z-10 h-[30px] w-[30px] items-center justify-center rounded-full ${done ? 'bg-[#1f8a3e]' : index === 3 ? 'bg-[#e08a2c]' : 'bg-[#e2e5e2]'}`}>
                  <Text className={`text-[13px] font-bold ${done || index === 3 ? 'text-white' : 'text-[#9aa39c]'}`}>{done ? '✓' : index === 3 ? '◷' : '▤'}</Text>
                </View>
                {index < milestones.length - 1 && <View className={`h-[38px] w-0.5 ${done ? 'bg-[#1f8a3e]' : 'bg-[#eceeec]'}`} />}
              </View>
              <View className="flex-1 pb-[22px]">
                <Text className="mb-0.5 text-sm font-bold">{title}</Text>
                <Text className="text-xs text-[#6b746e]">{subtitle}</Text>
              </View>
            </View>
          ))}
        </View>
      </Card>
      <Card>
        <Text className="mb-4 text-base font-bold">Mandi Live Snapshot</Text>
        <View className="flex-row gap-[10px]">
          <Snapshot value="142" label="Farmers Today" color="text-[#1f8a3e]" />
          <Snapshot value={String(booking.queue_info.vehicles_ahead)} label="In Queue" color="text-[#e08a2c]" />
          <Snapshot value="₹2,840" label="Avg. Price/Qtl" color="text-[#1f8a3e]" />
        </View>
      </Card>
    </>
  );
}

function Snapshot({ value, label, color }: { value: string; label: string; color: string }) {
  return (
    <View className="flex-1 items-center rounded-[14px] bg-[#f4f5f4] px-2 py-[14px]">
      <Text className={`mb-[3px] text-[18px] font-extrabold ${color}`}>{value}</Text>
      <Text className="text-center text-[10.5px] font-semibold text-[#6b746e]">{label}</Text>
    </View>
  );
}

function BottomNavigation({
  activePage,
  onNavigate,
}: {
  activePage: Page;
  onNavigate: (page: Page) => void;
}) {
  const items: { page: Page; icon: string; label: string }[] = [
    { page: 'home', icon: '⌂', label: 'Home' },
    { page: 'slots', icon: '▣', label: 'Slots' },
    { page: 'status', icon: '◷', label: 'Status' },
  ];

  return (
    <View className="absolute bottom-0 left-0 right-0 flex-row rounded-b-[42px] border-t border-[#eceeec] bg-white px-1 pb-5 pt-[10px]">
      {items.map((item) => (
        <TouchableOpacity className="flex-1 items-center gap-1" key={item.page} onPress={() => onNavigate(item.page)}>
          <Text className={`text-[22px] ${activePage === item.page ? 'text-[#1f8a3e]' : 'text-[#9aa39c]'}`}>{item.icon}</Text>
          <Text className={`text-[10.5px] font-semibold ${activePage === item.page ? 'text-[#1f8a3e]' : 'text-[#9aa39c]'}`}>{item.label}</Text>
        </TouchableOpacity>
      ))}
      <TouchableOpacity className="flex-1 items-center gap-1" onPress={() => undefined}>
        <Text className="text-[22px] text-[#9aa39c]">▢</Text>
        <Text className="text-[10.5px] font-semibold text-[#9aa39c]">Complaints</Text>
      </TouchableOpacity>
      <TouchableOpacity className="flex-1 items-center gap-1" onPress={() => undefined}>
        <Text className="text-[22px] text-[#9aa39c]">♙</Text>
        <Text className="text-[10.5px] font-semibold text-[#9aa39c]">Profile</Text>
      </TouchableOpacity>
    </View>
  );
}
