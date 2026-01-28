import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ArrowLeft, MessageCircle, CheckCircle, XCircle, Clock, AlertTriangle, Mail, Archive, Search } from 'lucide-react';
import { PaywallModal } from '../components/Paywall';

// Helper to get display name with i18n fallback
const getDisplayName = (user, t) => {
  if (!user) return t('profile.noName');
  return user.display_name || t('profile.noName');
};

// Reputation badge component
const ReputationBadge = ({ status, t }) => {
  const config = {
    new: { color: 'bg-blue-100 text-blue-800', icon: '🔵', label: t('reputation.new') },
    trusted: { color: 'bg-green-100 text-green-800', icon: '🟢', label: t('reputation.trusted') },
    under_review: { color: 'bg-yellow-100 text-yellow-800', icon: '🟡', label: t('reputation.underReview') },
    restricted: { color: 'bg-red-100 text-red-800', icon: '🔴', label: t('reputation.restricted') }
  };
  const c = config[status] || config.new;  // Default to "new" instead of "trusted"
  return (
    <Badge className={c.color}>
      <span className="mr-1">{c.icon}</span>
      {c.label}
    </Badge>
  );
};

// Exchange status badge
const ExchangeStatusBadge = ({ status, t }) => {
  const config = {
    pending: { color: 'bg-blue-100 text-blue-800', icon: <Clock className="h-3 w-3" />, label: t('exchange.statusPending') },
    completed: { color: 'bg-green-100 text-green-800', icon: <CheckCircle className="h-3 w-3" />, label: t('exchange.statusCompleted') },
    failed: { color: 'bg-red-100 text-red-800', icon: <XCircle className="h-3 w-3" />, label: t('exchange.statusFailed') },
    expired: { color: 'bg-gray-100 text-gray-800', icon: <AlertTriangle className="h-3 w-3" />, label: t('exchange.statusExpired') }
  };
  const c = config[status] || config.pending;
  return (
    <Badge className={`${c.color} flex items-center gap-1`}>
      {c.icon}
      {c.label}
    </Badge>
  );
};

// Failure reasons - Split into MINOR (no reputation impact) and SERIOUS
const FAILURE_REASONS_MINOR = [
  { value: 'schedule_conflict', labelKey: 'exchange.reasonScheduleConflict' },
  { value: 'personal_issue', labelKey: 'exchange.reasonPersonalIssue' },
  { value: 'moved_away', labelKey: 'exchange.reasonMovedAway' },
  { value: 'lost_stickers', labelKey: 'exchange.reasonLostStickers' }
];

const FAILURE_REASONS_SERIOUS = [
  { value: 'no_show', labelKey: 'exchange.reasonNoShow' },
  { value: 'cancelled_no_notice', labelKey: 'exchange.reasonCancelledNoNotice' },
  { value: 'attempted_sale', labelKey: 'exchange.reasonAttemptedSale' },
  { value: 'inappropriate', labelKey: 'exchange.reasonInappropriate' },
  { value: 'wrong_stickers', labelKey: 'exchange.reasonWrongStickers' }
];

// Exchange card component - outside of Exchanges to prevent re-rendering issues
const ExchangeCard = ({ exchange, isCompleted, onClick, t }) => (
  <Card 
    className={`cursor-pointer hover:shadow-lg transition-all ${
      !isCompleted && exchange.has_unread && exchange.status === 'pending' 
        ? 'border-2 border-primary' 
        : isCompleted ? 'opacity-80' : ''
    }`}
    onClick={onClick}
  >
    <CardContent className="p-3 sm:p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
          <div className={`h-10 w-10 sm:h-12 sm:w-12 rounded-full flex items-center justify-center font-bold relative flex-shrink-0 text-sm sm:text-base ${
            isCompleted ? 'bg-gray-400 text-white' : 'bg-primary text-primary-foreground'
          }`}>
            {getDisplayName(exchange.partner, t)[0].toUpperCase()}
            {/* Unread indicator dot - only for active */}
            {!isCompleted && exchange.has_unread && exchange.status === 'pending' && (
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full flex items-center justify-center text-[10px] text-white font-bold">
                {exchange.unread_count > 9 ? '9+' : exchange.unread_count}
              </span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className={`font-semibold text-sm sm:text-base truncate ${isCompleted ? 'text-muted-foreground' : ''}`}>
              {getDisplayName(exchange.partner, t)}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <ReputationBadge status={exchange.partner?.reputation_status} t={t} />
            </div>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <ExchangeStatusBadge status={exchange.status} t={t} />
          <p className="text-[10px] sm:text-xs text-muted-foreground mt-1">
            {isCompleted && exchange.completed_at 
              ? new Date(exchange.completed_at).toLocaleDateString()
              : new Date(exchange.created_at).toLocaleDateString()
            }
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
);

export const Exchanges = () => {
  const { albumId } = useParams();
  const [exchanges, setExchanges] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingMatches, setCheckingMatches] = useState(false);
  const [hasCheckedMatches, setHasCheckedMatches] = useState(false);
  const [activeTab, setActiveTab] = useState(null); // Will be set after data loads: 'new', 'active', or 'completed'
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [paywallReason, setPaywallReason] = useState(null);
  const [startingExchange, setStartingExchange] = useState(null); // Track which match is being started
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Filter exchanges by tab
  const activeStatuses = ['pending', 'new', 'in_progress'];
  const completedStatuses = ['completed', 'failed', 'expired'];
  
  const activeExchanges = exchanges
    .filter(ex => activeStatuses.includes(ex.status))
    .sort((a, b) => new Date(b.last_activity || b.created_at) - new Date(a.last_activity || a.created_at));
  
  const completedExchanges = exchanges
    .filter(ex => completedStatuses.includes(ex.status))
    .sort((a, b) => new Date(b.completed_at || b.created_at) - new Date(a.completed_at || a.created_at));

  // Badge conditions
  const hasNewMatches = matches.length > 0;
  const hasUnreadMessages = activeExchanges.some(ex => ex.has_unread && ex.status === 'pending');

  useEffect(() => {
    fetchExchanges();
  }, [albumId]);

  // Set default tab after data loads - ALWAYS default to "New exchanges"
  useEffect(() => {
    if (!loading && activeTab === null) {
      // Always default to "New exchanges" tab per user feedback
      setActiveTab('new');
    }
  }, [loading, activeTab]);

  // Handle starting an exchange directly from the New Exchanges tab
  const handleStartExchange = async (partnerUserId) => {
    setStartingExchange(partnerUserId);
    try {
      const response = await api.post(`/albums/${albumId}/exchanges`, {
        album_id: albumId,
        partner_user_id: partnerUserId
      });
      
      // Show appropriate message based on whether it's new or existing
      if (response.data.is_existing) {
        toast.success(t('exchange.exchangeExists'));
      } else {
        toast.success(t('exchange.exchangeCreated'));
      }
      
      // Navigate directly to the exchange detail
      navigate(`/exchanges/${response.data.exchange.id}`);
    } catch (error) {
      // Check for freemium limit error
      const errorDetail = error.response?.data?.detail;
      if (errorDetail?.code === 'DAILY_MATCH_LIMIT') {
        setPaywallReason('DAILY_MATCH_LIMIT');
        setPaywallOpen(true);
        return;
      }
      
      // Translate backend error codes to user-friendly messages
      const errorCode = typeof errorDetail === 'string' ? errorDetail : errorDetail?.code;
      const errorMessages = {
        'ALBUM_NOT_ACTIVATED': t('errors.albumNotActivated'),
        'PARTNER_NOT_FOUND': t('errors.partnerNotFound'),
        'ACCOUNT_RESTRICTED': t('errors.accountRestricted'),
        'PARTNER_NOT_AVAILABLE': t('errors.partnerNotAvailable'),
        'NO_MUTUAL_MATCH': t('errors.noMutualMatch')
      };
      toast.error(errorMessages[errorCode] || t('common.error'));
    } finally {
      setStartingExchange(null);
    }
  };

  const fetchExchanges = async () => {
    try {
      const response = await api.get(`/albums/${albumId}/exchanges`);
      setExchanges(response.data);
      
      // Always fetch matches to show badge on "New" tab
      await fetchMatches();
    } catch (error) {
      // Empty result is NOT an error - don't show error toast for 404 or empty
      // Only show toast for actual errors (500, network, etc.)
      if (error.response?.status >= 500) {
        toast.error(t('common.error'));
      }
      // For 404 or any other case, check for matches
      await fetchMatches();
    } finally {
      setLoading(false);
    }
  };

  const fetchMatches = async () => {
    setCheckingMatches(true);
    try {
      const response = await api.get(`/albums/${albumId}/matches`);
      setMatches(response.data);
      setHasCheckedMatches(true);
      // Don't navigate away - let user see the tabs
    } catch (error) {
      console.error('Failed to fetch matches:', error);
      setHasCheckedMatches(true);
    } finally {
      setCheckingMatches(false);
    }
  };

  // Show loading while fetching exchanges or checking matches

  // Show loading while fetching exchanges or checking matches
  if (loading || checkingMatches || activeTab === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="text-2xl font-bold text-primary mb-2">{t('common.loading')}</div>
          <p className="text-muted-foreground">
            {checkingMatches ? t('exchange.findMatches') + '...' : ''}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern pb-20 overflow-x-hidden">
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(`/albums/${albumId}`)}
            className="flex-shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl sm:text-3xl font-black tracking-tight text-primary truncate">{t('exchange.myExchanges')}</h1>
        </div>

        {/* 3-Tab Navigation */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          {/* Tab triggers - 3 equal sections */}
          <TabsList className="grid w-full grid-cols-3 mb-4 sm:mb-6">
            <TabsTrigger 
              value="new" 
              className="flex items-center justify-center gap-1 sm:gap-1.5 text-[11px] sm:text-sm px-1 sm:px-3"
              data-testid="tab-new"
            >
              <Search className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
              <span className="truncate">{t('exchange.tabNew')}</span>
              {hasNewMatches && (
                <Badge className="ml-0.5 sm:ml-1 h-4 w-4 sm:h-5 sm:w-5 p-0 flex items-center justify-center text-[9px] sm:text-[10px] bg-green-500 text-white flex-shrink-0">
                  {matches.length > 9 ? '9+' : matches.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="active" 
              className="flex items-center justify-center gap-1 sm:gap-1.5 text-[11px] sm:text-sm px-1 sm:px-3"
              data-testid="tab-active"
            >
              <MessageCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
              <span className="truncate">{t('exchange.tabActive')}</span>
              {hasUnreadMessages && (
                <Badge className="ml-0.5 sm:ml-1 h-4 w-4 sm:h-5 sm:w-5 p-0 flex items-center justify-center text-[9px] sm:text-[10px] bg-red-500 text-white animate-pulse flex-shrink-0">
                  !
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="completed" 
              className="flex items-center justify-center gap-1 sm:gap-1.5 text-[11px] sm:text-sm px-1 sm:px-3"
              data-testid="tab-completed"
            >
              <Archive className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
              <span className="truncate">{t('exchange.tabCompleted')}</span>
            </TabsTrigger>
          </TabsList>

          {/* New Exchanges Tab - Shows available matches */}
          <TabsContent value="new" className="mt-0">
            {matches.length === 0 ? (
              <div className="text-center py-10 sm:py-16 px-4">
                <Search className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-muted-foreground mb-3" />
                <h3 className="text-base sm:text-lg font-semibold mb-2">{t('exchange.noNewMatches')}</h3>
                <p className="text-xs sm:text-sm text-muted-foreground mb-4">{t('exchange.noNewMatchesHint')}</p>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => navigate(`/albums/${albumId}/inventory`)}
                >
                  {t('exchange.updateInventory')}
                </Button>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                <p className="text-xs sm:text-sm text-muted-foreground text-center mb-2">
                  {t('exchange.matchesFound', { count: matches.length })}
                </p>
                {matches.map((match) => (
                  <Card 
                    key={match.user.id}
                    data-testid={`match-card-${match.user.id}`}
                    className={`cursor-pointer hover:shadow-lg transition-all border-green-200 bg-green-50/30 ${startingExchange === match.user.id ? 'opacity-50' : ''}`}
                    onClick={() => !startingExchange && handleStartExchange(match.user.id)}
                  >
                    <CardContent className="p-3 sm:p-4">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                          <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-green-500 text-white flex items-center justify-center font-bold flex-shrink-0 text-sm sm:text-base">
                            {getDisplayName(match.user, t)[0].toUpperCase()}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-semibold text-sm sm:text-base truncate">
                              {getDisplayName(match.user, t)}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <ReputationBadge status={match.user?.reputation_status} t={t} />
                            </div>
                          </div>
                        </div>
                        {startingExchange === match.user.id ? (
                          <Badge className="bg-gray-100 text-gray-600 text-[10px] sm:text-xs flex-shrink-0">
                            {t('common.loading')}...
                          </Badge>
                        ) : (
                          <Badge className="bg-green-100 text-green-800 text-[10px] sm:text-xs flex-shrink-0">
                            {t('exchange.canExchange')}
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Active Exchanges Tab */}
          <TabsContent value="active" className="mt-0">
            {activeExchanges.length === 0 ? (
              <div className="text-center py-10 sm:py-16 px-4">
                <MessageCircle className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-muted-foreground mb-3" />
                <h3 className="text-base sm:text-lg font-semibold mb-2">{t('exchange.noActiveExchanges')}</h3>
                <p className="text-xs sm:text-sm text-muted-foreground mb-4">{t('exchange.noActiveExchangesHint')}</p>
                <Button onClick={() => setActiveTab('new')} size="sm">
                  {t('exchange.tabNew')}
                </Button>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {activeExchanges.map((exchange) => (
                  <ExchangeCard 
                    key={exchange.id} 
                    exchange={exchange} 
                    isCompleted={false} 
                    onClick={() => navigate(`/exchanges/${exchange.id}`)}
                    t={t}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Completed Exchanges Tab */}
          <TabsContent value="completed" className="mt-0">
            {completedExchanges.length === 0 ? (
              <div className="text-center py-10 sm:py-16 px-4">
                <Archive className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-muted-foreground mb-3" />
                <h3 className="text-base sm:text-lg font-semibold mb-2">{t('exchange.noCompletedExchanges')}</h3>
                <p className="text-xs sm:text-sm text-muted-foreground">{t('exchange.noCompletedExchangesHint')}</p>
              </div>
            ) : (
              <div className="space-y-3 sm:space-y-4">
                {completedExchanges.map((exchange) => (
                  <ExchangeCard 
                    key={exchange.id} 
                    exchange={exchange} 
                    isCompleted={true}
                    onClick={() => navigate(`/exchanges/${exchange.id}`)}
                    t={t}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export const ExchangeDetail = () => {
  const { exchangeId } = useParams();
  const [exchange, setExchange] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmType, setConfirmType] = useState(null); // 'success' or 'failure'
  const [failureReason, setFailureReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchExchange();
  }, [exchangeId]);

  const fetchExchange = async () => {
    try {
      const response = await api.get(`/exchanges/${exchangeId}`);
      setExchange(response.data);
    } catch (error) {
      // Don't show raw backend error
      toast.error(t('common.error'));
      // Navigate to albums if exchange not found (don't use navigate(-1))
      navigate('/albums');
    } finally {
      setLoading(false);
    }
  };
  
  // Get proper back navigation path
  const getBackPath = () => {
    if (exchange?.album_id) {
      return `/albums/${exchange.album_id}/exchanges`;
    }
    return '/albums';
  };

  const handleConfirm = async () => {
    if (confirmType === 'failure' && !failureReason) {
      toast.error(t('exchange.selectReason'));
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/exchanges/${exchangeId}/confirm`, {
        confirmed: confirmType === 'success',
        failure_reason: confirmType === 'failure' ? failureReason : null
      });
      toast.success(t('exchange.confirmationSaved'));
      setConfirmDialogOpen(false);
      fetchExchange();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const hasUserConfirmed = () => {
    if (!exchange) return false;
    return exchange.is_user_a ? exchange.user_a_confirmed !== null : exchange.user_b_confirmed !== null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl sm:text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  if (!exchange) return null;

  const myOffers = exchange.is_user_a ? exchange.user_a_offers_details : exchange.user_b_offers_details;
  const theirOffers = exchange.is_user_a ? exchange.user_b_offers_details : exchange.user_a_offers_details;

  return (
    <div className="min-h-screen sticker-album-pattern pb-20 overflow-x-hidden">
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex items-center gap-3 sm:gap-4 mb-4 sm:mb-6">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(getBackPath())}
            className="flex-shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg sm:text-2xl font-black tracking-tight text-primary truncate">{t('exchange.details')}</h1>
          </div>
          <ExchangeStatusBadge status={exchange.status} t={t} />
        </div>

        {/* Partner Info */}
        <Card className="mb-4 sm:mb-6">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg sm:text-xl flex-shrink-0">
                {getDisplayName(exchange.partner, t)[0].toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-base sm:text-xl font-semibold truncate">
                  {getDisplayName(exchange.partner, t)}
                </p>
                <ReputationBadge status={exchange.partner?.reputation_status} t={t} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stickers Exchange Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-6">
          <Card>
            <CardHeader className="pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
              <CardTitle className="text-xs sm:text-sm text-muted-foreground">{t('exchange.youGive')}</CardTitle>
            </CardHeader>
            <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
              <div className="space-y-1">
                {myOffers?.map((sticker) => (
                  <div key={sticker.id} className="text-xs sm:text-sm bg-amber-50 p-2 rounded">
                    N° {sticker.number} - {sticker.name}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2 px-3 sm:px-6 pt-3 sm:pt-6">
              <CardTitle className="text-xs sm:text-sm text-muted-foreground">{t('exchange.youReceive')}</CardTitle>
            </CardHeader>
            <CardContent className="px-3 sm:px-6 pb-3 sm:pb-6">
              <div className="space-y-1">
                {theirOffers?.map((sticker) => (
                  <div key={sticker.id} className="text-xs sm:text-sm bg-green-50 p-2 rounded">
                    N° {sticker.number} - {sticker.name}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chat Button */}
        <Button 
          className="w-full mb-3 sm:mb-4 text-sm sm:text-base"
          onClick={() => navigate(`/exchanges/${exchangeId}/chat`)}
        >
          <MessageCircle className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
          {exchange.status === 'pending' ? t('exchange.openChat') : t('exchange.viewChat')}
        </Button>

        {/* Confirmation Actions (only for pending exchanges) */}
        {exchange.status === 'pending' && !hasUserConfirmed() && (
          <Card className="border-2 border-dashed">
            <CardHeader className="pb-2 sm:pb-4 px-4 sm:px-6 pt-4 sm:pt-6">
              <CardTitle className="text-base sm:text-lg">{t('exchange.confirmTitle')}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 sm:px-6 pb-4 sm:pb-6">
              <p className="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">
                {t('exchange.confirmDescription')}
              </p>
              {/* Stack buttons on mobile, side by side on larger screens */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
                <Button 
                  className="w-full sm:flex-1 bg-green-600 hover:bg-green-700 text-sm sm:text-base py-3"
                  onClick={() => { setConfirmType('success'); setConfirmDialogOpen(true); }}
                >
                  <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 mr-2 flex-shrink-0" />
                  <span className="truncate">{t('exchange.confirmSuccess')}</span>
                </Button>
                <Button 
                  variant="destructive"
                  className="w-full sm:flex-1 text-sm sm:text-base py-3"
                  onClick={() => { setConfirmType('failure'); setConfirmDialogOpen(true); }}
                >
                  <XCircle className="h-4 w-4 sm:h-5 sm:w-5 mr-2 flex-shrink-0" />
                  <span className="truncate">{t('exchange.confirmFailure')}</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Already Confirmed Message */}
        {hasUserConfirmed() && (
          <Card className="bg-muted">
            <CardContent className="p-4 text-center">
              <CheckCircle className="h-8 w-8 mx-auto text-green-600 mb-2" />
              <p className="font-semibold">{t('exchange.alreadyConfirmed')}</p>
            </CardContent>
          </Card>
        )}

        {/* Confirmation Dialog */}
        <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {confirmType === 'success' ? t('exchange.confirmSuccessTitle') : t('exchange.confirmFailureTitle')}
              </DialogTitle>
              <DialogDescription>
                {confirmType === 'success' 
                  ? t('exchange.confirmSuccessDesc')
                  : t('exchange.confirmFailureDesc')
                }
              </DialogDescription>
            </DialogHeader>

            {confirmType === 'failure' && (
              <div className="space-y-3">
                <p className="text-sm font-semibold">{t('exchange.selectReasonLabel')}</p>
                
                {/* Minor issues - No reputation impact */}
                <p className="text-xs text-muted-foreground font-medium mt-2">{t('exchange.minorIssuesTitle')}</p>
                {FAILURE_REASONS_MINOR.map((reason) => (
                  <div 
                    key={reason.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      failureReason === reason.value 
                        ? 'border-amber-500 bg-amber-50' 
                        : 'hover:border-gray-400'
                    }`}
                    onClick={() => setFailureReason(reason.value)}
                  >
                    <p className="text-sm">{t(reason.labelKey)}</p>
                  </div>
                ))}
                
                {/* Serious issues - Affects reputation */}
                <p className="text-xs text-muted-foreground font-medium mt-3">{t('exchange.seriousIssuesTitle')}</p>
                {FAILURE_REASONS_SERIOUS.map((reason) => (
                  <div 
                    key={reason.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      failureReason === reason.value 
                        ? 'border-red-500 bg-red-50' 
                        : 'hover:border-gray-400'
                    }`}
                    onClick={() => setFailureReason(reason.value)}
                  >
                    <p className="text-sm">{t(reason.labelKey)}</p>
                  </div>
                ))}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmDialogOpen(false)}>
                {t('common.cancel')}
              </Button>
              <Button 
                onClick={handleConfirm}
                disabled={submitting || (confirmType === 'failure' && !failureReason)}
                className={confirmType === 'success' ? 'bg-green-600 hover:bg-green-700' : ''}
                variant={confirmType === 'failure' ? 'destructive' : 'default'}
              >
                {submitting ? t('common.loading') : t('common.confirm')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Exchanges;
