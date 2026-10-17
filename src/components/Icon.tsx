import {
  ArrowRight,
  CalendarBlank,
  CaretDown,
  Check,
  MapPin,
  MagnifyingGlass,
  Minus,
  Package,
  Plus,
  Truck,
  UserCircle,
  Wallet,
  X,
} from '@phosphor-icons/react';
import type { ComponentType } from 'react';
import type { IconProps as PhosphorIconProps } from '@phosphor-icons/react';

export type IconName = 'search' | 'arrow' | 'plus' | 'minus' | 'check' | 'close' | 'pin' | 'calendar' | 'truck' | 'box' | 'chevron' | 'wallet' | 'user';

const icons = {
  search: MagnifyingGlass,
  arrow: ArrowRight,
  plus: Plus,
  minus: Minus,
  check: Check,
  close: X,
  pin: MapPin,
  calendar: CalendarBlank,
  truck: Truck,
  box: Package,
  chevron: CaretDown,
  wallet: Wallet,
  user: UserCircle,
} satisfies Record<IconName, ComponentType<PhosphorIconProps>>;

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  weight?: PhosphorIconProps['weight'];
}

export function Icon({ name, size = 20, className, weight = 'regular' }: IconProps) {
  const PhosphorIcon = icons[name];
  return <PhosphorIcon className={className ? `icon ${className}` : 'icon'} size={size} weight={weight} aria-hidden="true" focusable="false" />;
}
