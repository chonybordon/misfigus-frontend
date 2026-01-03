import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ArrowLeft, Send, CheckCircle, XCircle, MessageCircle } from 'lucide-react';

export const Offers = () => {
  const { groupId } = useParams();
  const location = useLocation();
  const [offers, setOffers] = useState({ sent: [], received: [] });
  const [loading, setLoading] = useState(true);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchOffers();
  }, [groupId]);

  useEffect(() => {
    if (location.state) {
      handleCreateOfferFromMatch();
    }
  }, [location.state]);

  const fetchOffers = async () => {
    try {
      const response = await api.get(`/offers?group_id=${groupId}`);
      setOffers(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOfferFromMatch = async () => {
    if (!location.state) return;

    try {
      await api.post('/offers', {
        group_id: groupId,
        to_user_id: location.state.to_user_id,
        give_items: location.state.give_items,
        get_items: location.state.get_items,
      });
      toast.success(t('common.success'));
      fetchOffers();
      navigate(location.pathname, { replace: true, state: {} });
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleUpdateOffer = async (offerId, status) => {
    try {
      await api.patch(`/offers/${offerId}`, { status });
      toast.success(t('common.success'));
      
      if (status === 'accepted') {
        const offer = offers.received.find((o) => o.id === offerId);
        setSelectedOffer(offer);
        setConfirmDialogOpen(true);
      }
      
      fetchOffers();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleApplyOffer = async () => {
    if (!selectedOffer) return;

    try {
      await api.post(`/offers/${selectedOffer.id}/apply`);
      toast.success(t('common.success'));
      setConfirmDialogOpen(false);
      fetchOffers();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      sent: 'bg-blue-100 text-blue-800',
      accepted: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      countered: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };

    return (
      <Badge className={variants[status]}>
        {t(`offers.status.${status}`)}
      </Badge>
    );
  };

  const OfferCard = ({ offer, type }) => (
    <Card data-testid={`offer-card-${offer.id}`} className="hover:shadow-lg transition-all">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
              {(type === 'sent' ? offer.to_user : offer.from_user)?.full_name[0].toUpperCase()}
            </div>
            <span>{(type === 'sent' ? offer.to_user : offer.from_user)?.full_name}</span>
          </div>
          {getStatusBadge(offer.status)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-semibold text-muted-foreground mb-2">
              {type === 'sent' ? t('matches.youGive') : t('matches.youGet')}
            </p>
            <div className="space-y-1">
              {offer.items
                .filter((item) => item.direction === 'give')
                .map((item, idx) => (
                  <div key={idx} className="text-sm bg-muted p-2 rounded">
                    Sticker #{item.sticker_id} (x{item.qty})
                  </div>
                ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold text-muted-foreground mb-2">
              {type === 'sent' ? t('matches.youGet') : t('matches.youGive')}
            </p>
            <div className="space-y-1">
              {offer.items
                .filter((item) => item.direction === 'get')
                .map((item, idx) => (
                  <div key={idx} className="text-sm bg-muted p-2 rounded">
                    Sticker #{item.sticker_id} (x{item.qty})
                  </div>
                ))}
            </div>
          </div>
        </div>

        {type === 'received' && offer.status === 'sent' && (
          <div className="flex gap-2 mt-4">
            <Button
              data-testid={`accept-offer-btn-${offer.id}`}
              className="flex-1 btn-accent"
              onClick={() => handleUpdateOffer(offer.id, 'accepted')}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              {t('offers.accept')}
            </Button>
            <Button
              data-testid={`reject-offer-btn-${offer.id}`}
              variant="outline"
              className="flex-1"
              onClick={() => handleUpdateOffer(offer.id, 'rejected')}
            >
              <XCircle className="h-4 w-4 mr-2" />
              {t('offers.reject')}
            </Button>
          </div>
        )}

        <Button
          data-testid={`chat-offer-btn-${offer.id}`}
          variant="outline"
          className="w-full mt-2"
          onClick={() =>
            navigate(`/groups/${groupId}/chat/${type === 'sent' ? offer.to_user_id : offer.from_user_id}`)
          }
        >
          <MessageCircle className="h-4 w-4 mr-2" />
          {t('chat.title')}
        </Button>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-group-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(`/groups/${groupId}`)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('offers.title')}</h1>
        </div>

        <Tabs defaultValue="received" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger data-testid="tab-received" value="received">
              {t('offers.received')} ({offers.received.length})
            </TabsTrigger>
            <TabsTrigger data-testid="tab-sent" value="sent">
              {t('offers.sent')} ({offers.sent.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="received" className="space-y-4" data-testid="received-offers-list">
            {offers.received.length === 0 ? (
              <div className="text-center py-20 text-muted-foreground">
                {t('matches.noMatches')}
              </div>
            ) : (
              offers.received.map((offer) => <OfferCard key={offer.id} offer={offer} type="received" />)
            )}
          </TabsContent>

          <TabsContent value="sent" className="space-y-4" data-testid="sent-offers-list">
            {offers.sent.length === 0 ? (
              <div className="text-center py-20 text-muted-foreground">
                {t('matches.noMatches')}
              </div>
            ) : (
              offers.sent.map((offer) => <OfferCard key={offer.id} offer={offer} type="sent" />)
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
          <DialogContent data-testid="confirm-inventory-dialog">
            <DialogHeader>
              <DialogTitle>{t('offers.updateInventory')}</DialogTitle>
            </DialogHeader>
            <div className="flex gap-4">
              <Button
                data-testid="apply-offer-yes-btn"
                className="flex-1 btn-primary"
                onClick={handleApplyOffer}
              >
                {t('offers.yes')}
              </Button>
              <Button
                data-testid="apply-offer-later-btn"
                variant="outline"
                className="flex-1"
                onClick={() => setConfirmDialogOpen(false)}
              >
                {t('offers.later')}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Offers;
