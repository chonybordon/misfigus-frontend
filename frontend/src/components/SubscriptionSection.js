import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Crown, Check, X, AlertTriangle, Sparkles, Calendar, Album, MessageCircle, Megaphone, Star, Infinity, Package } from 'lucide-react';

// Plan benefit item component
const BenefitItem = ({ icon: Icon, text, included = true, comingSoon = false, small = false }) => (
  <div className={`flex items-center gap-2 ${small ? 'text-xs' : 'text-xs sm:text-sm'}`}>
    {included ? (
      <Check className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-green-500 flex-shrink-0`} />
    ) : (
      <X className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-gray-300 flex-shrink-0`} />
    )}
    <Icon className={`${small ? 'w-3 h-3' : 'w-3.5 h-3.5 sm:w-4 sm:h-4'} text-muted-foreground flex-shrink-0`} />
    <span className={included ? '' : 'text-gray-400'}>
      {text}
      {comingSoon && <span className="text-[10px] text-muted-foreground ml-1">({comingSoon})</span>}
    </span>
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

  // TEMPORARY: Set to false when payments go live
  const showComingSoon = true;

  return (
    <button
      className={`w-full p-3 sm:p-4 rounded-lg border-2 text-left transition-all duration-200 relative ${getCardStyle()}`}
      onClick={() => !isCurrentPlan && !disabled && onSelect?.()}
      disabled={isCurrentPlan || disabled}
    >
      {/* Recommended badge - only on Plus, uses Plus brand color */}
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
      {/* Selected indicator - checkmark in plan color */}
      {isSelected && !isCurrentPlan && (
        <div className={`absolute top-3 right-3 w-6 h-6 rounded-full flex items-center justify-center ${colors.checkBg} shadow-md`}>
          <Check className="w-4 h-4 text-white" />
        </div>
      )}
      
      {/* Plan name - highlighted when selected */}
      <div className={`font-bold text-base sm:text-lg mb-3 ${isSelected && !isCurrentPlan ? colors.text : ''}`}>
        {name}
      </div>
      
      {/* Benefits list */}
      <div className="space-y-1.5">
        {benefits.map((benefit, idx) => (
          <BenefitItem key={idx} {...benefit} small />
        ))}
      </div>
      
      {/* Coming Soon notice - easily removable when payments go live */}
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

export const SubscriptionSection = ({ onPlanChange }) => {
  const { t } = useTranslation();
  const [planStatus, setPlanStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [showDowngradeDialog, setShowDowngradeDialog] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);
  const [selectedUpgradePlan, setSelectedUpgradePlan] = useState(null);

  useEffect(() => {
    fetchPlanStatus();
  }, []);

  const fetchPlanStatus = async () => {
    try {
      const response = await api.get('/user/plan-status');
      setPlanStatus(response.data);
    } catch (error) {
      toast.error(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (targetPlan) => {
    setUpgrading(true);
    try {
      await api.post(`/user/set-plan?plan=${targetPlan}&plan_type=monthly`);
      toast.success(t('premium.upgradeSuccess'));
      await fetchPlanStatus();
      onPlanChange?.();
      setShowUpgradeDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail?.message || error.response?.data?.detail || t('common.error'));
    } finally {
      setUpgrading(false);
    }
  };

  const handleDowngrade = async () => {
    setDowngrading(true);
    try {
      await api.post('/user/set-plan?plan=free');
      toast.success(t('subscription.downgradeSuccess'));
      await fetchPlanStatus();
      onPlanChange?.();
      setShowDowngradeDialog(false);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail?.code === 'TOO_MANY_ALBUMS') {
        toast.error(t('subscription.downgradeBlocked'));
      } else {
        toast.error(detail?.message || t('common.error'));
      }
    } finally {
      setDowngrading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Card data-testid="subscription-section">
        <CardContent className="p-4 sm:p-6">
          <div className="animate-pulse space-y-3 sm:space-y-4">
            <div className="h-5 sm:h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!planStatus) return null;

  const currentPlan = planStatus.plan || 'free';
  const isPaid = currentPlan === 'plus' || currentPlan === 'unlimited';
  const canDowngradeToFree = planStatus.can_downgrade_to_free;

  // Plan display name mapping
  const getPlanDisplayName = (plan) => {
    switch (plan) {
      case 'free': return t('subscription.free');
      case 'plus': return t('subscription.plus');
      case 'unlimited': return t('subscription.unlimited');
      default: return t('subscription.free');
    }
  };

  // Get benefits based on current plan
  const getCurrentPlanBenefits = () => {
    switch (currentPlan) {
      case 'unlimited':
        return [
          { icon: Album, text: t('subscription.unlimitedBenefits.albums'), included: true },
          { icon: MessageCircle, text: t('subscription.unlimitedBenefits.chats'), included: true },
          { icon: Megaphone, text: t('subscription.unlimitedBenefits.noAds'), included: true },
        ];
      case 'plus':
        return [
          { icon: Album, text: t('subscription.plusBenefits.albums'), included: true },
          { icon: MessageCircle, text: t('subscription.plusBenefits.chats'), included: true },
          { icon: Megaphone, text: t('subscription.plusBenefits.noAds'), included: true },
        ];
      default: // free
        return [
          { icon: Album, text: t('subscription.freeBenefits.albums'), included: true },
          { icon: MessageCircle, text: t('subscription.freeBenefits.chats'), included: true },
          { icon: Check, text: t('subscription.freeBenefits.inventory'), included: true },
        ];
    }
  };

  // Get plan badge color
  const getPlanBadgeStyle = () => {
    switch (currentPlan) {
      case 'unlimited':
        return 'bg-gradient-to-r from-purple-600 to-pink-600';
      case 'plus':
        return 'bg-gradient-to-r from-blue-500 to-cyan-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <>
      <Card data-testid="subscription-section" className="border-2 border-primary/20">
        <CardHeader className="pb-2 sm:pb-3 px-4 sm:px-6 pt-4 sm:pt-6">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <Crown className={`w-4 h-4 sm:w-5 sm:h-5 ${isPaid ? 'text-yellow-500' : 'text-gray-400'}`} />
              <span className="truncate">{t('subscription.title')}</span>
            </CardTitle>
            <Badge className={`${getPlanBadgeStyle()} text-white text-xs flex-shrink-0`}>
              {currentPlan === 'unlimited' && <Infinity className="w-3 h-3 mr-1" />}
              {currentPlan === 'plus' && <Sparkles className="w-3 h-3 mr-1" />}
              {getPlanDisplayName(currentPlan)}
            </Badge>
          </div>
          <CardDescription className="text-xs sm:text-sm">
            {t('subscription.currentPlan')}: {getPlanDisplayName(currentPlan)}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4 sm:space-y-6 px-4 sm:px-6 pb-4 sm:pb-6">
          {/* Premium Until for paid plans */}
          {isPaid && planStatus.premium_until && (
            <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground bg-green-50 p-2 sm:p-3 rounded-lg">
              <Calendar className="w-4 h-4 text-green-600 flex-shrink-0" />
              <span className="text-green-700">
                {t('subscription.activeUntil')}: <strong>{formatDate(planStatus.premium_until)}</strong>
              </span>
            </div>
          )}

          {/* Current Plan Benefits */}
          <div>
            <h4 className="font-medium mb-2 sm:mb-3 text-xs sm:text-sm text-muted-foreground uppercase tracking-wide">
              {t('subscription.benefits') || 'Beneficios de tu plan'}
            </h4>
            <div className="space-y-1.5 sm:space-y-2">
              {getCurrentPlanBenefits().map((benefit, idx) => (
                <BenefitItem key={idx} {...benefit} />
              ))}
            </div>
          </div>

          {/* Usage Stats */}
          <div className="bg-gray-50 p-3 sm:p-4 rounded-lg space-y-1.5 sm:space-y-2">
            <div className="flex justify-between text-xs sm:text-sm">
              <span>{t('subscription.freeBenefits.albums')}</span>
              <span className="font-medium">
                {planStatus.active_albums} / {planStatus.albums_limit || '∞'}
              </span>
            </div>
            <div className="flex justify-between text-xs sm:text-sm">
              <span>{t('subscription.freeBenefits.chats')}</span>
              <span className="font-medium">
                {planStatus.matches_used_today} / {planStatus.matches_limit || '∞'}
              </span>
            </div>
            <p className="text-[10px] sm:text-xs text-muted-foreground pt-1">
              {t('subscription.unlimitedMessages')}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2 sm:space-y-3 pt-2">
            {currentPlan === 'free' && (
              <Button
                data-testid="upgrade-btn"
                className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-sm sm:text-base"
                onClick={() => setShowUpgradeDialog(true)}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {t('subscription.upgradeToPlus')}
              </Button>
            )}
            
            {currentPlan === 'plus' && (
              <>
                <Button
                  data-testid="upgrade-unlimited-btn"
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-sm sm:text-base"
                  onClick={() => {
                    setSelectedUpgradePlan('unlimited');
                    setShowUpgradeDialog(true);
                  }}
                >
                  <Infinity className="w-4 h-4 mr-2" />
                  {t('subscription.upgradeToUnlimited')}
                </Button>
                <Button
                  data-testid="downgrade-btn"
                  variant="outline"
                  className="w-full text-sm sm:text-base"
                  onClick={() => setShowDowngradeDialog(true)}
                  disabled={!canDowngradeToFree}
                >
                  {t('subscription.downgrade')}
                </Button>
              </>
            )}

            {currentPlan === 'unlimited' && (
              <Button
                data-testid="downgrade-btn"
                variant="outline"
                className="w-full text-sm sm:text-base"
                onClick={() => setShowDowngradeDialog(true)}
                disabled={!canDowngradeToFree}
              >
                {t('subscription.downgrade')}
              </Button>
            )}
            
            {/* Downgrade blocked message */}
            {isPaid && !canDowngradeToFree && (
              <div className="flex items-start gap-2 p-2 sm:p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs sm:text-sm">
                <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="text-yellow-800 min-w-0">
                  <p className="font-medium">{t('subscription.downgradeBlocked')}</p>
                  <p className="text-yellow-700 mt-1">
                    {t('subscription.deactivateFirst')}
                  </p>
                  <p className="text-yellow-600 mt-1 text-xs">
                    {t('subscription.currentlyActive', { count: planStatus.active_albums })} {t('subscription.freeAlbumLimit')}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Dialog */}
      <AlertDialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <Sparkles className={`w-5 h-5 ${selectedUpgradePlan === 'unlimited' ? 'text-purple-500' : 'text-blue-500'}`} />
              {t('subscription.upgrade')}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-left">
              {t('subscription.planComparison')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="space-y-3 py-4">
            {/* Plus Plan */}
            <PlanCard
              name={t('subscription.plus')}
              planKey="plus"
              isCurrentPlan={currentPlan === 'plus'}
              isSelected={selectedUpgradePlan === 'plus'}
              isRecommended={currentPlan === 'free'}
              benefits={[
                { icon: Album, text: t('subscription.plusBenefits.albums'), included: true },
                { icon: MessageCircle, text: t('subscription.plusBenefits.chats'), included: true },
                { icon: Package, text: t('subscription.plusBenefits.inventory'), included: true },
                { icon: Megaphone, text: t('subscription.plusBenefits.noAds'), included: true },
              ]}
              onSelect={() => setSelectedUpgradePlan('plus')}
              t={t}
            />
            
            {/* Unlimited Plan */}
            <PlanCard
              name={t('subscription.unlimited')}
              planKey="unlimited"
              isCurrentPlan={currentPlan === 'unlimited'}
              isSelected={selectedUpgradePlan === 'unlimited'}
              isRecommended={false}
              benefits={[
                { icon: Album, text: t('subscription.unlimitedBenefits.albums'), included: true },
                { icon: MessageCircle, text: t('subscription.unlimitedBenefits.chats'), included: true },
                { icon: Package, text: t('subscription.unlimitedBenefits.inventory'), included: true },
                { icon: Megaphone, text: t('subscription.unlimitedBenefits.noAds'), included: true },
              ]}
              onSelect={() => setSelectedUpgradePlan('unlimited')}
              t={t}
            />
          </div>

          <AlertDialogFooter className="flex-col sm:flex-row gap-2">
            <AlertDialogCancel className="w-full sm:w-auto">{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => handleUpgrade(selectedUpgradePlan)}
              disabled={upgrading || !selectedUpgradePlan || currentPlan === selectedUpgradePlan}
              className={`w-full sm:w-auto transition-all duration-200 ${
                selectedUpgradePlan === 'unlimited' 
                  ? 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600'
                  : selectedUpgradePlan === 'plus'
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600'
                    : 'bg-gray-400 hover:bg-gray-500'
              }`}
            >
              {selectedUpgradePlan === 'unlimited' && <Infinity className="w-4 h-4 mr-2" />}
              {selectedUpgradePlan === 'plus' && <Sparkles className="w-4 h-4 mr-2" />}
              {upgrading 
                ? t('common.loading') 
                : selectedUpgradePlan === 'unlimited' 
                  ? t('subscription.upgradeToUnlimited') 
                  : selectedUpgradePlan === 'plus'
                    ? t('subscription.upgradeToPlus')
                    : t('subscription.upgrade')
              }
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Downgrade Dialog */}
      <AlertDialog open={showDowngradeDialog} onOpenChange={setShowDowngradeDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              {t('subscription.confirmDowngrade') || 'Cambiar a plan gratuito'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t('subscription.downgradeWarning')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDowngrade}
              disabled={downgrading}
              className="bg-gray-600 hover:bg-gray-700"
            >
              {downgrading ? t('common.loading') : t('subscription.downgrade')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default SubscriptionSection;
