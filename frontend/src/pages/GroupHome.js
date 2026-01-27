import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Users, Package, UserPlus, Settings, Mail } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

// Helper to get translated album name from nameKey
const getAlbumNameDisplay = (album, t) => {
  if (album?.name_key) {
    return t(`albumNames.${album.name_key}`);
  }
  return album?.name || '';
};

const maskEmail = (email) => {
  if (!email) return '';
  const [local, domain] = email.split('@');
  if (local.length <= 3) {
    return `${local[0]}***@${domain}`;
  }
  return `${local.substring(0, 3)}***@${domain}`;
};

const getDisplayName = (user, t) => {
  if (!user) return t('app.defaultUser');
  if (user.display_name && user.display_name.trim()) {
    return user.display_name.trim();
  }
  if (user.email) {
    return maskEmail(user.email);
  }
  return t('app.defaultUser');
};

export const GroupHome = () => {
  const { groupId } = useParams();
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviting, setInviting] = useState(false);
  const [inviteSent, setInviteSent] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchGroup();
  }, [groupId]);

  const fetchGroup = async () => {
    try {
      const response = await api.get(`/groups/${groupId}`);
      setGroup(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
      navigate('/groups');
    } finally {
      setLoading(false);
    }
  };

  const handleSendInvite = async () => {
    if (!inviteEmail.trim()) return;
    
    setInviting(true);
    try {
      await api.post(`/groups/${groupId}/invite`, { email: inviteEmail.trim() });
      setInviteSent(true);
      toast.success(t('groups.inviteSent'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setInviting(false);
    }
  };

  const resetInviteDialog = () => {
    setInviteDialogOpen(false);
    setInviteEmail('');
    setInviteSent(false);
  };

  const memberCount = group?.member_count ?? 0;

  const getMemberCountDisplay = () => {
    if (memberCount === 0) {
      return `0 ${t('groups.memberPlural')}`;
    } else if (memberCount === 1) {
      return `1 ${t('groups.member')}`;
    } else {
      return `${memberCount} ${t('groups.memberPlural')}`;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-groups-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/groups')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-black tracking-tight text-primary">{group?.name}</h1>
            <p className="text-muted-foreground">
              {group?.album?.name} • {getMemberCountDisplay()}
            </p>
          </div>
          {group?.is_owner && (
            <Badge className="bg-amber-100 text-amber-700">{t('groups.owner')}</Badge>
          )}
        </div>

        {group?.album?.has_placeholder && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-900">
              {t('groups.placeholderBanner')}
            </p>
          </div>
        )}

        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">{t('groups.progress')}</span>
            <span className="text-sm font-bold text-primary">{group?.progress || 0}%</span>
          </div>
          <Progress value={group?.progress || 0} className="h-3" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Card
            data-testid="inventory-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/groups/${groupId}/inventory`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                {t('groups.myInventory')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('groups.manageInventory')}
              </p>
            </CardContent>
          </Card>

          <Card
            data-testid="matches-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/groups/${groupId}/matches`)}
          >
            <CardHeader>
              <CardTitle>{t('groups.matches')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('groups.findExchanges')}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card data-testid="members-card" className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {t('groups.members')}
              </div>
              {memberCount > 0 && (
                <Button
                  data-testid="view-all-members-btn"
                  variant="outline"
                  size="sm"
                  onClick={() => setMembersDialogOpen(true)}
                >
                  {t('groups.viewAll')}
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {memberCount === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>{t('groups.noOtherMembers')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {group?.members?.slice(0, 6).map((member) => (
                  <div key={member.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                      {getDisplayName(member, t)[0].toUpperCase()}
                    </div>
                    <span className="text-sm font-medium truncate">{getDisplayName(member, t)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Button
          data-testid="invite-member-btn"
          onClick={() => setInviteDialogOpen(true)}
          className="w-full btn-secondary"
        >
          <UserPlus className="h-5 w-5 mr-2" />
          {t('groups.inviteMember')}
        </Button>

        {/* Invite Dialog - Email only, no code shown */}
        <Dialog open={inviteDialogOpen} onOpenChange={resetInviteDialog}>
          <DialogContent data-testid="invite-dialog">
            <DialogHeader>
              <DialogTitle>{t('groups.inviteTitle')}</DialogTitle>
              <DialogDescription>{t('groups.inviteDescription')}</DialogDescription>
            </DialogHeader>
            
            {!inviteSent ? (
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">{t('groups.inviteEmail')}</label>
                  <Input
                    data-testid="invite-email-input"
                    type="email"
                    placeholder="amigo@email.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                  />
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
                  <p className="text-blue-800">
                    {t('groups.inviteNote')}
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center">
                <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-8 w-8 text-green-600" />
                </div>
                <p className="text-lg font-semibold text-green-800">{t('groups.inviteSentTitle')}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {t('groups.inviteSentDescription').replace('{email}', inviteEmail)}
                </p>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={resetInviteDialog}>
                {inviteSent ? t('common.close') : t('common.cancel')}
              </Button>
              {!inviteSent && (
                <Button
                  data-testid="send-invite-btn"
                  onClick={handleSendInvite}
                  disabled={inviting || !inviteEmail.trim()}
                  className="btn-primary"
                >
                  {inviting ? t('common.loading') : t('groups.sendInvite')}
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Members Dialog */}
        <Dialog open={membersDialogOpen} onOpenChange={setMembersDialogOpen}>
          <DialogContent data-testid="members-dialog" className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{t('groups.allMembers')}</DialogTitle>
            </DialogHeader>
            <div className="max-h-[60vh] overflow-y-auto">
              <div className="space-y-2">
                {group?.members?.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 rounded-lg bg-muted">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                        {getDisplayName(member, t)[0].toUpperCase()}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold">{getDisplayName(member, t)}</p>
                        <p className="text-xs text-muted-foreground">{maskEmail(member.email)}</p>
                      </div>
                    </div>
                    <Badge variant="secondary">
                      {t('groups.memberBadge')}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default GroupHome;
