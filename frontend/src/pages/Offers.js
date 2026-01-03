import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Send } from 'lucide-react';

const getDisplayName = (user, t) => {
  if (!user) return t('app.defaultUser');
  if (user.full_name && user.full_name !== user.email.split('@')[0]) {
    return user.full_name;
  }
  if (user.email) {
    return user.email.split('@')[0];
  }
  return t('app.defaultUser');
};

export const Offers = () => {
  const { albumId } = useParams();
  const [offers, setOffers] = useState({ sent: [], received: [] });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchOffers();
  }, [albumId]);

  const fetchOffers = async () => {
    try {
      const response = await api.get(`/offers?album_id=${albumId}`);
      setOffers(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOffer = async (offerId, status) => {
    try {
      await api.patch(`/offers/${offerId}`, { status });
      toast.success(t('common.success'));
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
    };

    return (
      <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>
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
              {getDisplayName(type === 'sent' ? offer.to_user : offer.from_user, t)[0].toUpperCase()}
            </div>
            <span>{getDisplayName(type === 'sent' ? offer.to_user : offer.from_user, t)}</span>
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
                    {t('offers.sticker')} #{item.sticker_id.slice(-4)} (x{item.qty})
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
                    Figurita #{item.sticker_id.slice(-4)} (x{item.qty})
                  </div>
                ))}
            </div>
          </div>
        </div>

        {type === 'received' && offer.status === 'sent' && (
          <div className="flex gap-2 mt-4">
            <Button
              data-testid={`accept-offer-btn-${offer.id}`}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
              onClick={() => handleUpdateOffer(offer.id, 'accepted')}
            >
              {t('offers.accept')}
            </Button>
            <Button
              data-testid={`reject-offer-btn-${offer.id}`}
              variant="outline"
              className="flex-1"
              onClick={() => handleUpdateOffer(offer.id, 'rejected')}
            >
              {t('offers.reject')}
            </Button>
          </div>
        )}
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
    <div className="min-h-screen sticker-album-pattern pb-20">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-album-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(`/albums/${albumId}`)}
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
      </div>
    </div>
  );
};

export default Offers;
