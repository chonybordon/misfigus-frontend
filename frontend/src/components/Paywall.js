import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Crown, Check, Infinity, Album, MessageCircle, Ban, Sparkles } from 'lucide-react';

// Paywall modal component
export const PaywallModal = ({ isOpen, onClose, reason, onUpgradeSuccess }) => {
  const [selectedPlan, setSelectedPlan] = useState('yearly');
  const [upgrading, setUpgrading] = useState(false);
  const { t } = useTranslation();

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      // FOR TESTING: This directly sets premium
      // In production, this would trigger payment flow
      const response = await api.post('/user/upgrade-premium');
      
      // Update cached user
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      currentUser.plan = 'premium';
      localStorage.setItem('user', JSON.stringify(currentUser));
      
      toast.success(t('premium.upgradeSuccess'));
      
      if (onUpgradeSuccess) {
        onUpgradeSuccess(response.data.user);
      }
      onClose();
    } catch (error) {
      toast.error(t('common.error'));
    } finally {
      setUpgrading(false);
    }
  };

  const getReasonTitle = () => {
    switch (reason) {
      case 'ALBUM_LIMIT':
        return t('premium.albumLimitTitle');
      case 'DAILY_MATCH_LIMIT':
        return t('premium.matchLimitTitle');
      default:
        return t('premium.title');
    }
  };

  const getReasonDescription = () => {
    switch (reason) {
      case 'ALBUM_LIMIT':
        return t('premium.albumLimitDesc');
      case 'DAILY_MATCH_LIMIT':
        return t('premium.matchLimitDesc');
      default:
        return t('premium.subtitle');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-[95vw] max-w-md mx-auto max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="mx-auto h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center mb-3 sm:mb-4">
            <Crown className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
          </div>
          <DialogTitle className="text-xl sm:text-2xl text-center">{getReasonTitle()}</DialogTitle>
          <DialogDescription className="text-center text-sm sm:text-base">
            {getReasonDescription()}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 sm:space-y-4 py-3 sm:py-4">
          {/* Premium Benefits */}
          <div className="space-y-2 sm:space-y-3">
            <div className="flex items-center gap-2 sm:gap-3 p-2 sm:p-3 bg-muted rounded-lg">
              <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Album className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">{t('premium.unlimitedAlbums')}</p>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">{t('premium.unlimitedAlbumsDesc')}</p>
              </div>
              <Check className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0" />
            </div>

            <div className="flex items-center gap-2 sm:gap-3 p-2 sm:p-3 bg-muted rounded-lg">
              <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <MessageCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">{t('premium.unlimitedMatches')}</p>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">{t('premium.unlimitedMatchesDesc')}</p>
              </div>
              <Check className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0" />
            </div>

            <div className="flex items-center gap-2 sm:gap-3 p-2 sm:p-3 bg-muted rounded-lg">
              <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Infinity className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">{t('premium.unlimitedInventory')}</p>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">{t('premium.alreadyIncluded')}</p>
              </div>
              <Check className="h-4 w-4 sm:h-5 sm:w-5 text-green-500 flex-shrink-0" />
            </div>

            <div className="flex items-center gap-2 sm:gap-3 p-2 sm:p-3 bg-muted rounded-lg opacity-60">
              <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Ban className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">{t('premium.noAds')}</p>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">{t('premium.comingSoon')}</p>
              </div>
              <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground flex-shrink-0" />
            </div>
          </div>

          {/* Plan Selection (UI only for now) */}
          <div className="grid grid-cols-2 gap-2 sm:gap-3 pt-3 sm:pt-4">
            <button
              onClick={() => setSelectedPlan('monthly')}
              className={`p-3 sm:p-4 rounded-lg border-2 transition-all text-center ${
                selectedPlan === 'monthly'
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <p className="font-bold text-base sm:text-lg">{t('premium.monthly')}</p>
              <p className="text-xs sm:text-sm text-muted-foreground">$X.XX/mes</p>
            </button>

            <button
              onClick={() => setSelectedPlan('yearly')}
              className={`p-3 sm:p-4 rounded-lg border-2 transition-all text-center relative ${
                selectedPlan === 'yearly'
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <span className="absolute -top-2 left-1/2 -translate-x-1/2 bg-green-500 text-white text-[10px] sm:text-xs px-2 py-0.5 rounded-full whitespace-nowrap">
                {t('premium.bestValue')}
              </span>
              <p className="font-bold text-base sm:text-lg">{t('premium.yearly')}</p>
              <p className="text-xs sm:text-sm text-muted-foreground">$XX.XX/año</p>
            </button>
          </div>
        </div>

        <div className="space-y-2 sm:space-y-3">
          <Button
            onClick={handleUpgrade}
            disabled={upgrading}
            className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold text-sm sm:text-base"
          >
            <Crown className="h-4 w-4 mr-2" />
            {upgrading ? t('common.loading') : t('premium.upgrade')}
          </Button>

          <Button
            variant="ghost"
            onClick={onClose}
            className="w-full text-sm sm:text-base"
          >
            {t('premium.notNow')}
          </Button>

          <p className="text-[10px] sm:text-xs text-center text-muted-foreground">
            {t('premium.freePlanNote')}
          </p>

          <p className="text-[10px] sm:text-xs text-center text-muted-foreground">
            <a href="/terms" className="underline">{t('terms.title')}</a>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Plan status badge component
export const PlanBadge = ({ plan, className = '' }) => {
  const { t } = useTranslation();
  
  if (plan === 'premium') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-yellow-500 to-orange-500 text-white ${className}`}>
        <Crown className="h-3 w-3" />
        Premium
      </span>
    );
  }
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground ${className}`}>
      Free
    </span>
  );
};

// Admin toggle for testing (only visible to admin emails)
export const AdminPlanToggle = ({ user, onPlanChange }) => {
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  
  // Only show for admin emails (add your test emails here)
  const adminEmails = ['admin@misfigus.com', 'test@misfigus.com'];
  if (!user || !adminEmails.includes(user.email)) {
    return null;
  }

  const togglePlan = async () => {
    setLoading(true);
    try {
      const newPlan = user.plan === 'premium' ? 'free' : 'premium';
      const endpoint = newPlan === 'premium' ? '/user/upgrade-premium' : '/user/downgrade-free';
      const response = await api.post(endpoint);
      
      // Update cached user
      const updatedUser = response.data.user;
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      toast.success(`Plan cambiado a ${newPlan}`);
      
      if (onPlanChange) {
        onPlanChange(updatedUser);
      }
    } catch (error) {
      toast.error('Error al cambiar plan');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-dashed border-2 border-yellow-500/50 bg-yellow-50/50">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-yellow-700">🔧 Admin Test Mode</p>
            <p className="text-sm text-yellow-600">Current: {user.plan || 'free'}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={togglePlan}
            disabled={loading}
            className="border-yellow-500 text-yellow-700"
          >
            {loading ? '...' : `Set to ${user.plan === 'premium' ? 'Free' : 'Premium'}`}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default PaywallModal;
