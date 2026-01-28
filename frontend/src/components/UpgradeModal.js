import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Check, Sparkles, Album, MessageCircle, Megaphone, Star, Infinity, Package } from 'lucide-react';

// Plan benefit item component
const BenefitItem = ({ icon: Icon, text, included = true, small = false }) => (
  <div className={`flex items-center gap-2 ${small ? 'text-xs' : 'text-xs sm:text-sm'}`}>
    {included ? (
      <Check className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-green-500 flex-shrink-0`} />
    ) : (
      <span className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-gray-300 flex-shrink-0`} />
    )}
    <Icon className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-muted-foreground flex-shrink-0`} />
    <span className={included ? '' : 'text-gray-400'}>{text}</span>
  </div>
);

// Plan card component for selection
const PlanCard = ({ 
  name, 
  planKey,
  benefits, 
  isCurrentPlan,
  isSelected,
  isRecommended, 
  onSelect, 
  disabled,
  t 
}) => {
  // Plan-specific color schemes
  const planColors = {
    plus: {
      border: 'border-blue-500',
      bg: 'bg-blue-50',
      ring: 'ring-blue-500/30',
      text: 'text-blue-600',
      badge: 'bg-gradient-to-r from-blue-500 to-cyan-500',
      checkBg: 'bg-blue-500'
    },
    unlimited: {
      border: 'border-purple-500',
      bg: 'bg-purple-50',
      ring: 'ring-purple-500/30',
      text: 'text-purple-600',
      badge: 'bg-gradient-to-r from-purple-600 to-purple-500',
      checkBg: 'bg-purple-500'
    }
  };

  const colors = planColors[planKey] || planColors.plus;

  // Determine card styling based on state
  const getCardStyle = () => {
    if (isCurrentPlan) {
      return 'border-green-500 bg-green-50/50 cursor-default';
    }
    if (isSelected) {
      return `${colors.border} ${colors.bg} ring-2 ${colors.ring} shadow-lg cursor-pointer`;
    }
    if (disabled) {
      return 'border-gray-200 opacity-50 cursor-not-allowed';
    }
    return 'border-gray-200 hover:border-gray-300 hover:shadow-sm cursor-pointer';
  };

  // Show coming soon notice for payments
  const showComingSoon = true;

  return (
    <button
      className={`w-full p-3 sm:p-4 rounded-lg border-2 text-left transition-all duration-200 relative ${getCardStyle()}`}
      onClick={() => !isCurrentPlan && !disabled && onSelect?.()}
      disabled={isCurrentPlan || disabled}
    >
      {/* Recommended badge */}
      {isRecommended && !isCurrentPlan && planKey === 'plus' && (
        <Badge className={`absolute -top-2 left-1/2 -translate-x-1/2 ${colors.badge} text-[10px] whitespace-nowrap text-white`}>
          <Star className="w-3 h-3 mr-1" />
          {t('subscription.recommended')}
        </Badge>
      )}
      {/* Current plan badge */}
      {isCurrentPlan && (
        <Badge className="absolute -top-2 right-2 bg-green-500 text-[10px] text-white">
          {t('subscription.currentPlan')}
        </Badge>
      )}
      {/* Selected indicator */}
      {isSelected && !isCurrentPlan && (
        <div className={`absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center ${colors.checkBg} shadow-md`}>
          <Check className="w-4 h-4 text-white" />
        </div>
      )}
      
      {/* Plan name */}
      <div className={`font-bold text-base sm:text-lg mb-3 ${isSelected && !isCurrentPlan ? colors.text : ''}`}>
        {name}
      </div>
      
      {/* Benefits list */}
      <div className="space-y-1.5">
        {benefits.map((benefit, idx) => (
          <BenefitItem key={idx} {...benefit} small />
        ))}
      </div>
      
      {/* Coming Soon notice */}
      {showComingSoon && !isCurrentPlan && !disabled && (
        <div className="mt-3 pt-2 border-t border-gray-100">
          <span className="text-xs text-muted-foreground italic">
            {t('subscription.comingSoon')}
          </span>
        </div>
      )}
    </button>
  );
};

/**
 * Unified Upgrade Modal Component
 * 
 * This component replaces the old PaywallModal and provides a consistent
 * upgrade experience using the new Plus/Unlimited plan system.
 * 
 * @param {boolean} isOpen - Whether the modal is open
 * @param {function} onClose - Callback when modal is closed
 * @param {string} reason - The reason for showing the modal ('ALBUM_LIMIT' | 'DAILY_CHAT_LIMIT')
 * @param {function} onUpgradeSuccess - Callback when upgrade is successful
 * @param {string} currentPlan - The user's current plan ('free' | 'plus' | 'unlimited')
 */
export const UpgradeModal = ({ 
  isOpen, 
  onClose, 
  reason = null, 
  onUpgradeSuccess,
  currentPlan = 'free'
}) => {
  const { t } = useTranslation();
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [upgrading, setUpgrading] = useState(false);

  // Reset selection when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedPlan(null);
    }
  }, [isOpen]);

  const handleUpgrade = async () => {
    if (!selectedPlan) return;
    
    setUpgrading(true);
    try {
      await api.post(`/user/set-plan?plan=${selectedPlan}&plan_type=monthly`);
      
      // Update cached user
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      currentUser.plan = selectedPlan;
      localStorage.setItem('user', JSON.stringify(currentUser));
      
      toast.success(t('subscription.upgradeSuccess') || t('premium.upgradeSuccess'));
      
      if (onUpgradeSuccess) {
        onUpgradeSuccess(selectedPlan);
      }
      onClose();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(detail?.message || detail || t('common.error'));
    } finally {
      setUpgrading(false);
    }
  };

  // Get contextual title based on reason
  const getTitle = () => {
    switch (reason) {
      case 'ALBUM_LIMIT':
        return t('upgrade.albumLimitTitle') || t('subscription.upgrade');
      case 'DAILY_CHAT_LIMIT':
        return t('upgrade.chatLimitTitle') || t('subscription.upgrade');
      default:
        return t('subscription.upgrade');
    }
  };

  // Get contextual description based on reason
  const getDescription = () => {
    switch (reason) {
      case 'ALBUM_LIMIT':
        return t('upgrade.albumLimitDesc');
      case 'DAILY_CHAT_LIMIT':
        return t('upgrade.chatLimitDesc');
      default:
        return t('subscription.planComparison');
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Sparkles className={`w-5 h-5 ${selectedPlan === 'unlimited' ? 'text-purple-500' : 'text-blue-500'}`} />
            {getTitle()}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-left">
            {getDescription()}
          </AlertDialogDescription>
        </AlertDialogHeader>
        
        <div className="space-y-3 py-4">
          {/* Plus Plan */}
          <PlanCard
            name={t('subscription.plus')}
            planKey="plus"
            isCurrentPlan={currentPlan === 'plus'}
            isSelected={selectedPlan === 'plus'}
            isRecommended={currentPlan === 'free'}
            benefits={[
              { icon: Album, text: t('subscription.plusBenefits.albums'), included: true },
              { icon: MessageCircle, text: t('subscription.plusBenefits.chats'), included: true },
              { icon: Package, text: t('subscription.plusBenefits.inventory'), included: true },
              { icon: Megaphone, text: t('subscription.plusBenefits.noAds'), included: true },
            ]}
            onSelect={() => setSelectedPlan('plus')}
            t={t}
          />
          
          {/* Unlimited Plan */}
          <PlanCard
            name={t('subscription.unlimited')}
            planKey="unlimited"
            isCurrentPlan={currentPlan === 'unlimited'}
            isSelected={selectedPlan === 'unlimited'}
            isRecommended={false}
            benefits={[
              { icon: Album, text: t('subscription.unlimitedBenefits.albums'), included: true },
              { icon: MessageCircle, text: t('subscription.unlimitedBenefits.chats'), included: true },
              { icon: Package, text: t('subscription.unlimitedBenefits.inventory'), included: true },
              { icon: Megaphone, text: t('subscription.unlimitedBenefits.noAds'), included: true },
            ]}
            onSelect={() => setSelectedPlan('unlimited')}
            t={t}
          />
        </div>

        <AlertDialogFooter className="flex-col sm:flex-row gap-2">
          <AlertDialogCancel className="w-full sm:w-auto">{t('common.cancel')}</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleUpgrade}
            disabled={upgrading || !selectedPlan || currentPlan === selectedPlan}
            className={`w-full sm:w-auto transition-all duration-200 ${
              selectedPlan === 'unlimited' 
                ? 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600'
                : selectedPlan === 'plus'
                  ? 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600'
                  : 'bg-gray-400 hover:bg-gray-500'
            }`}
          >
            {selectedPlan === 'unlimited' && <Infinity className="w-4 h-4 mr-2" />}
            {selectedPlan === 'plus' && <Sparkles className="w-4 h-4 mr-2" />}
            {upgrading 
              ? t('common.loading') 
              : selectedPlan === 'unlimited' 
                ? t('subscription.upgradeToUnlimited') 
                : selectedPlan === 'plus'
                  ? t('subscription.upgradeToPlus')
                  : t('subscription.upgrade')
            }
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default UpgradeModal;
