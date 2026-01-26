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
import { Crown, Check, X, AlertTriangle, Sparkles, Calendar, Album, Repeat, Megaphone } from 'lucide-react';

export const SubscriptionSection = ({ onPlanChange }) => {
  const { t } = useTranslation();
  const [planStatus, setPlanStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [showDowngradeDialog, setShowDowngradeDialog] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);
  const [selectedPlanType, setSelectedPlanType] = useState('monthly');

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

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      await api.post(`/user/upgrade-premium?plan_type=${selectedPlanType}`);
      toast.success(t('premium.upgradeSuccess'));
      await fetchPlanStatus();
      onPlanChange?.();
      setShowUpgradeDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setUpgrading(false);
    }
  };

  const handleDowngrade = async () => {
    setDowngrading(true);
    try {
      await api.post('/user/downgrade-free');
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

  const isPremium = planStatus.is_premium;
  const canDowngrade = planStatus.can_downgrade;

  return (
    <>
      <Card data-testid="subscription-section" className="border-2 border-primary/20">
        <CardHeader className="pb-2 sm:pb-3 px-4 sm:px-6 pt-4 sm:pt-6">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <Crown className={`w-4 h-4 sm:w-5 sm:h-5 ${isPremium ? 'text-yellow-500' : 'text-gray-400'}`} />
              <span className="truncate">{t('subscription.title')}</span>
            </CardTitle>
            {isPremium && (
              <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white text-xs flex-shrink-0">
                <Sparkles className="w-3 h-3 mr-1" />
                Premium
              </Badge>
            )}
          </div>
          <CardDescription className="text-xs sm:text-sm">
            {t('subscription.currentPlan')}: {isPremium ? t('subscription.premiumPlan') : t('subscription.freePlan')}
            {isPremium && planStatus.plan_type && (
              <span className="ml-1 sm:ml-2">
                ({planStatus.plan_type === 'annual' ? t('subscription.annual') : t('subscription.monthly')})
              </span>
            )}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4 sm:space-y-6 px-4 sm:px-6 pb-4 sm:pb-6">
          {/* Premium Until */}
          {isPremium && planStatus.premium_until && (
            <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground bg-green-50 p-2 sm:p-3 rounded-lg">
              <Calendar className="w-4 h-4 text-green-600 flex-shrink-0" />
              <span className="text-green-700">
                {t('subscription.activeUntil')}: <strong>{formatDate(planStatus.premium_until)}</strong>
              </span>
            </div>
          )}

          {/* Benefits Section */}
          <div>
            <h4 className="font-medium mb-2 sm:mb-3 text-xs sm:text-sm text-muted-foreground uppercase tracking-wide">
              {t('subscription.benefits')}
            </h4>
            <div className="space-y-1.5 sm:space-y-2">
              {isPremium ? (
                <>
                  <BenefitItem icon={Album} text={t('subscription.premiumBenefits.albums')} included />
                  <BenefitItem icon={Repeat} text={t('subscription.premiumBenefits.matches')} included />
                  <BenefitItem icon={Megaphone} text={t('subscription.premiumBenefits.noAds')} included comingSoon />
                </>
              ) : (
                <>
                  <BenefitItem icon={Album} text={t('subscription.freeBenefits.albums')} included />
                  <BenefitItem icon={Repeat} text={t('subscription.freeBenefits.matches')} included />
                  <BenefitItem icon={Check} text={t('subscription.freeBenefits.inventory')} included />
                </>
              )}
            </div>
          </div>

          {/* Usage Stats for Free Users */}
          {!isPremium && (
            <div className="bg-gray-50 p-4 rounded-lg space-y-2">
              <div className="flex justify-between text-sm">
                <span>{t('subscription.freeBenefits.albums')}</span>
                <span className="font-medium">
                  {planStatus.active_albums} / {planStatus.albums_limit}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>{t('subscription.freeBenefits.matches')}</span>
                <span className="font-medium">
                  {planStatus.matches_used_today} / {planStatus.matches_limit}
                </span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3 pt-2">
            {!isPremium ? (
              <Button
                data-testid="upgrade-btn"
                className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600"
                onClick={() => setShowUpgradeDialog(true)}
              >
                <Crown className="w-4 h-4 mr-2" />
                {t('subscription.upgradeToPremium')}
              </Button>
            ) : (
              <Button
                data-testid="downgrade-btn"
                variant="outline"
                className="w-full"
                onClick={() => setShowDowngradeDialog(true)}
                disabled={!canDowngrade}
              >
                {t('subscription.downgradeToFree')}
              </Button>
            )}
            
            {/* Downgrade blocked message */}
            {isPremium && !canDowngrade && (
              <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm">
                <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="text-yellow-800">
                  <p className="font-medium">{t('subscription.downgradeBlocked')}</p>
                  <p className="text-yellow-700 mt-1">
                    {t('subscription.currentlyActive', { count: planStatus.active_albums })} {t('subscription.deactivateFirst')}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Dialog */}
      <AlertDialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-yellow-500" />
              {t('subscription.upgradeToPremium')}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              {/* Plan Type Selection */}
              <div className="grid grid-cols-2 gap-3 mt-4">
                <button
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    selectedPlanType === 'monthly' 
                      ? 'border-primary bg-primary/5' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedPlanType('monthly')}
                >
                  <div className="font-medium">{t('subscription.monthly')}</div>
                  <div className="text-sm text-muted-foreground">30 {t('common.days') || 'días'}</div>
                </button>
                <button
                  className={`p-4 rounded-lg border-2 text-left transition-all relative ${
                    selectedPlanType === 'annual' 
                      ? 'border-primary bg-primary/5' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedPlanType('annual')}
                >
                  <Badge className="absolute -top-2 -right-2 bg-green-500 text-xs">
                    {t('premium.bestValue')}
                  </Badge>
                  <div className="font-medium">{t('subscription.annual')}</div>
                  <div className="text-sm text-muted-foreground">365 {t('common.days') || 'días'}</div>
                </button>
              </div>
              
              {/* Benefits preview */}
              <div className="bg-gray-50 p-4 rounded-lg space-y-2 mt-4">
                <BenefitItem icon={Album} text={t('subscription.premiumBenefits.albums')} included small />
                <BenefitItem icon={Repeat} text={t('subscription.premiumBenefits.matches')} included small />
                <BenefitItem icon={Megaphone} text={t('subscription.premiumBenefits.noAds')} included small comingSoon />
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleUpgrade}
              disabled={upgrading}
              className="bg-gradient-to-r from-yellow-500 to-orange-500"
            >
              {upgrading ? t('common.loading') : t('subscription.upgradeToPremium')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Downgrade Confirmation Dialog */}
      <AlertDialog open={showDowngradeDialog} onOpenChange={setShowDowngradeDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('subscription.confirmDowngrade')}</AlertDialogTitle>
            <AlertDialogDescription>
              <p>{t('subscription.confirmDowngradeDesc')}</p>
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                {t('subscription.downgradeWarning')}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDowngrade}
              disabled={downgrading}
              className="bg-red-500 hover:bg-red-600"
            >
              {downgrading ? t('common.loading') : t('subscription.downgradeToFree')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

// Benefit item component
const BenefitItem = ({ icon: Icon, text, included, comingSoon, small }) => (
  <div className={`flex items-center gap-2 ${small ? 'text-sm' : ''}`}>
    {included ? (
      <Check className={`${small ? 'w-3 h-3' : 'w-4 h-4'} text-green-500`} />
    ) : (
      <X className={`${small ? 'w-3 h-3' : 'w-4 h-4'} text-gray-300`} />
    )}
    <Icon className={`${small ? 'w-3 h-3' : 'w-4 h-4'} text-muted-foreground`} />
    <span className={included ? '' : 'text-muted-foreground'}>
      {text}
      {comingSoon && <span className="text-xs text-muted-foreground ml-1">*</span>}
    </span>
  </div>
);

export default SubscriptionSection;
