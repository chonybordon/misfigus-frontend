import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ArrowRight, TrendingUp } from 'lucide-react';

export const Matches = () => {
  const { groupId, albumId } = useParams();
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchMatches();
  }, [groupId, albumId]);

  const fetchMatches = async () => {
    try {
      const response = await api.get(`/matches?group_id=${groupId}&album_id=${albumId}`);
      setMatches(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOffer = (match) => {
    navigate(`/groups/${groupId}/offers`, {
      state: {
        to_user_id: match.user.id,
        give_items: match.give_stickers.map((s) => ({ sticker_id: s.id, qty: 1 })),
        get_items: match.get_stickers.map((s) => ({ sticker_id: s.id, qty: 1 })),
      },
    });
  };

  const directMatches = matches.filter((m) => m.type === 'direct');
  const partialMatches = matches.filter((m) => m.type === 'partial');

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
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('matches.title')}</h1>
        </div>

        {matches.length === 0 ? (
          <div className="text-center py-20" data-testid="no-matches-message">
            <TrendingUp className="h-24 w-24 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">{t('matches.noMatches')}</h2>
            <p className="text-muted-foreground mb-6">{t('matches.findMore')}</p>
            <Button
              className="btn-primary"
              onClick={() => navigate(`/groups/${groupId}/albums/${albumId}/inventory`)}
            >
              {t('inventory.title')}
            </Button>
          </div>
        ) : (
          <Tabs defaultValue="direct" className="space-y-6">
            <TabsList>
              <TabsTrigger data-testid="tab-direct" value="direct">
                {t('matches.direct')} ({directMatches.length})
              </TabsTrigger>
              <TabsTrigger data-testid="tab-partial" value="partial">
                {t('matches.partial')} ({partialMatches.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="direct" className="space-y-4" data-testid="direct-matches-list">
              {directMatches.map((match, index) => (
                <Card key={index} data-testid={`match-card-${index}`} className="hover:shadow-lg transition-all">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                          {match.user.full_name[0].toUpperCase()}
                        </div>
                        <span>{match.user.full_name}</span>
                      </div>
                      {match.net_gain >= 0 && (
                        <Badge className="bg-accent text-accent-foreground" data-testid={`net-gain-badge-${index}`}>
                          {t('matches.netGain')}: +{match.net_gain}
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                      <div>
                        <p className="text-sm font-semibold text-muted-foreground mb-2">{t('matches.youGive')}</p>
                        <div className="space-y-1">
                          {match.give_stickers.map((s) => (
                            <div key={s.id} className="text-sm bg-amber-100 dark:bg-amber-900/30 p-2 rounded">
                              #{s.number} {s.name}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex justify-center">
                        <ArrowRight className="h-8 w-8 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-muted-foreground mb-2">{t('matches.youGet')}</p>
                        <div className="space-y-1">
                          {match.get_stickers.map((s) => (
                            <div key={s.id} className="text-sm bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded">
                              #{s.number} {s.name}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <Button
                      data-testid={`create-offer-btn-${index}`}
                      className="w-full mt-4 btn-primary"
                      onClick={() => handleCreateOffer(match)}
                    >
                      {t('matches.createOffer')}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="partial" className="space-y-4" data-testid="partial-matches-list">
              {partialMatches.map((match, index) => (
                <Card key={index} data-testid={`partial-match-card-${index}`} className="hover:shadow-lg transition-all">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        {match.user.full_name[0].toUpperCase()}
                      </div>
                      <span>{match.user.full_name}</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div>
                      <p className="text-sm font-semibold text-muted-foreground mb-2">{t('matches.youGive')}</p>
                      <div className="space-y-1">
                        {match.give_stickers.map((s) => (
                          <div key={s.id} className="text-sm bg-amber-100 dark:bg-amber-900/30 p-2 rounded">
                            #{s.number} {s.name}
                          </div>
                        ))}
                      </div>
                    </div>
                    <Button
                      data-testid={`create-partial-offer-btn-${index}`}
                      className="w-full mt-4 btn-secondary"
                      onClick={() => handleCreateOffer(match)}
                    >
                      {t('matches.createOffer')}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
};

export default Matches;
